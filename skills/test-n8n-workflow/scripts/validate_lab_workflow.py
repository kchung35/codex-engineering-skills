#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

from n8n_api import load_lab_config

PURE_LOCAL_TYPES = {
    "n8n-nodes-base.webhook", "n8n-nodes-base.respondToWebhook", "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.set", "n8n-nodes-base.code", "n8n-nodes-base.function",
    "n8n-nodes-base.functionItem", "n8n-nodes-base.if", "n8n-nodes-base.switch",
    "n8n-nodes-base.merge", "n8n-nodes-base.splitInBatches", "n8n-nodes-base.aggregate",
    "n8n-nodes-base.itemLists", "n8n-nodes-base.dateTime", "n8n-nodes-base.crypto",
    "n8n-nodes-base.sort", "n8n-nodes-base.limit", "n8n-nodes-base.removeDuplicates",
    "n8n-nodes-base.noOp", "n8n-nodes-base.stickyNote",
}

SUSPICIOUS_CODE = re.compile(
    r"\brequire\s*\(|\bimport\s+|\bfetch\s*\(|\baxios\b|\brequests\b|\burllib\b|"
    r"\bprocess\.env\b|\$env\b|\bchild_process\b|\bsubprocess\b|\bos\.environ\b|"
    r"\bsocket\b|\bhttps?\.|\bhttpRequest\b|\bfs\.|\bopen\s*\(", re.IGNORECASE,
)
ALLOWED_CLASSES = {"LOCAL", "READ_ONLY", "TEST_TARGET", "STUBBED", "WRITE_ALLOWED", "DENY"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_trigger_like(node):
    t = str(node.get("type", "")).lower()
    name = str(node.get("name", ""))
    return ("trigger" in t or t.endswith(".webhook") or t.endswith(".form") or
            t.endswith(".formtrigger") or name == "LAB Fixture Trigger")


def is_intrinsically_local(node):
    t = node.get("type")
    if t not in PURE_LOCAL_TYPES:
        return False
    if t in {"n8n-nodes-base.code", "n8n-nodes-base.function", "n8n-nodes-base.functionItem"}:
        params = node.get("parameters") or {}
        code = " ".join(str(params.get(k, "")) for k in ("jsCode", "pythonCode", "functionCode", "functionItemCode"))
        if SUSPICIOUS_CODE.search(code):
            return False
    return True


def validate_workflow(cfg, workflow, manifest, ack_writes=False):
    errors, warnings = [], []
    prefix = cfg.get("workflow_name_prefix", "LAB__")
    name = workflow.get("name", "")
    if not isinstance(name, str) or not name.startswith(prefix):
        errors.append(f"workflow name must start with configured prefix {prefix!r}")

    nodes = workflow.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("workflow.nodes must be a non-empty array")
        return errors, warnings, {}
    names = [n.get("name") for n in nodes]
    if len(names) != len(set(names)):
        errors.append("workflow node names must be unique")

    enabled_triggers = [n for n in nodes if is_trigger_like(n) and not n.get("disabled", False)]
    lab_triggers = [n for n in enabled_triggers if n.get("name") == "LAB Fixture Trigger" and n.get("type") == "n8n-nodes-base.webhook"]
    if len(lab_triggers) != 1:
        errors.append("BOUNDARY_REPLAY lab workflow must contain exactly one enabled LAB Fixture Trigger webhook")
    other_enabled = [n.get("name") for n in enabled_triggers if n.get("name") != "LAB Fixture Trigger"]
    if other_enabled:
        errors.append("unexpected enabled trigger-like nodes: " + ", ".join(map(str, other_enabled)))

    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        errors.append("side-effect manifest must be a schema_version=1 JSON object")
        entries = {}
    else:
        entries = manifest.get("nodes") or {}
        if not isinstance(entries, dict):
            errors.append("side-effect manifest nodes must be an object")
            entries = {}

    classification_report = {}
    node_by_name = {n.get("name"): n for n in nodes}
    for node in nodes:
        node_name = node.get("name")
        intrinsic = is_intrinsically_local(node)
        entry = entries.get(node_name)
        if intrinsic and entry is None:
            classification_report[node_name] = "LOCAL(auto)"
            continue
        if not isinstance(entry, dict):
            errors.append(f"node {node_name!r} is not intrinsically local and lacks side-effect classification")
            continue
        cls = entry.get("classification")
        reason = entry.get("reason")
        if cls not in ALLOWED_CLASSES:
            errors.append(f"node {node_name!r} has invalid classification {cls!r}")
            continue
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"node {node_name!r} classification requires a reason")
        classification_report[node_name] = cls
        if cls == "LOCAL" and not intrinsic:
            errors.append(f"node {node_name!r} is classified LOCAL but is not in the intrinsically-local allowlist")
        if cls == "DENY":
            errors.append(f"node {node_name!r} is classified DENY")
        if cls == "TEST_TARGET":
            target = entry.get("target")
            allowed_targets = set(cfg.get("allowed_test_targets") or [])
            if not isinstance(target, str) or not target.strip():
                errors.append(f"node {node_name!r} TEST_TARGET classification requires a target alias")
            elif target not in allowed_targets:
                errors.append(f"node {node_name!r} TEST_TARGET alias {target!r} is not in allowed_test_targets")
        if cls == "WRITE_ALLOWED":
            if cfg.get("allow_external_writes") is not True:
                errors.append(f"node {node_name!r} requests WRITE_ALLOWED but lab config forbids external writes")
            if not ack_writes:
                errors.append(f"node {node_name!r} requests WRITE_ALLOWED but explicit --ack-writes was not provided")
        if cls == "STUBBED" and not (intrinsic or node.get("disabled", False)):
            errors.append(f"node {node_name!r} is STUBBED but actual node is neither local nor disabled")
        if node.get("type") == "n8n-nodes-base.httpRequest":
            params = node.get("parameters") or {}
            method = str(params.get("method", "GET")).upper()
            if cls == "READ_ONLY" and method not in {"GET", "HEAD"}:
                errors.append(f"HTTP node {node_name!r} classified READ_ONLY but method is {method}")
            url = params.get("url")
            if isinstance(url, str) and not url.strip().startswith("="):
                host = (urllib.parse.urlparse(url).hostname or "").lower()
                for denied in cfg.get("external_deny_hosts", []):
                    d = str(denied).strip().lower()
                    if d and (host == d or host.endswith("." + d)):
                        errors.append(f"HTTP node {node_name!r} targets denied external host {host!r}")

    for entry_name in entries:
        if entry_name not in node_by_name:
            warnings.append(f"side-effect manifest contains node not present in workflow: {entry_name!r}")
    if cfg.get("project_id") and workflow.get("projectId") != cfg.get("project_id"):
        errors.append("workflow projectId does not match configured lab project_id")
    return errors, warnings, classification_report


def main():
    p = argparse.ArgumentParser(description="Validate an ephemeral n8n lab workflow before deployment")
    p.add_argument("--config", required=True)
    p.add_argument("--workflow", required=True)
    p.add_argument("--side-effects", required=True)
    p.add_argument("--ack-writes", action="store_true")
    args = p.parse_args()
    cfg = load_lab_config(args.config)
    workflow = load_json(args.workflow)
    manifest = load_json(args.side_effects)
    errors, warnings, report = validate_workflow(cfg, workflow, manifest, ack_writes=args.ack_writes)
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"PASS: lab workflow safety gate nodes={len(workflow.get('nodes', []))}")
    for name, cls in report.items():
        print(f"  {name}: {cls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
