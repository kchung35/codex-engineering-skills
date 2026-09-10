#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from typing import Any

from common import load_json, node_key, write_json

BASE_LENSES = {"requirements", "scope-diff"}
BEHAVIOR_LENSES = {"data-flow", "n8n-semantics", "regression", "test-adequacy"}
LOCAL_TOKENS = {
    "set", "editfields", "if", "switch", "merge", "code", "function", "functionitem",
    "itemlists", "splitout", "aggregate", "summarize", "filter", "sort", "limit", "noop",
    "datetime", "crypto", "comparedatasets", "removeduplicates", "renamekeys", "splitinbatches",
    "loopoveritems", "stopanderror", "manualtrigger", "respondtowebhook",
}
WRITE_HTTP_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
WRITE_SQL = re.compile(r"\b(insert|update|delete|merge|upsert|replace|drop|alter|truncate|create)\b", re.I)


def short_type(node: dict[str, Any]) -> str:
    value = str(node.get("type", ""))
    return value.rsplit(".", 1)[-1].lower()


def is_local(node: dict[str, Any]) -> bool:
    return short_type(node) in LOCAL_TOKENS


def add_signal(signals: list[dict[str, Any]], sid: str, severity: str, lenses: list[str], reason: str, node: str | None = None) -> None:
    item = {"id": sid, "severity": severity, "lenses": lenses, "reason": reason}
    if node:
        item["node"] = node
    signals.append(item)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic review-risk routing signals from an n8n candidate and semantic diff")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        candidate = load_json(args.candidate)
        diff = load_json(args.diff)
        if diff.get("schema_version") != 1:
            raise ValueError("diff must have schema_version=1")
        nodes = {node_key(n): n for n in candidate.get("nodes", []) or [] if isinstance(n, dict)}
        changed_keys = {x.get("key") for x in diff.get("nodes", {}).get("added", [])}
        changed_keys |= {x.get("key") for x in diff.get("nodes", {}).get("modified", [])}
        signals: list[dict[str, Any]] = []
        required = set(BASE_LENSES)
        if diff.get("behavioral_changed"):
            required |= set(BEHAVIOR_LENSES)

        if diff.get("connections_changed"):
            add_signal(signals, "CONTROL_FLOW_CHANGED", "MEDIUM", ["n8n-semantics", "regression"], "Workflow connections changed")
        if diff.get("static_data_changed"):
            add_signal(signals, "STATIC_STATE_CHANGED", "HIGH", ["state-idempotency", "regression"], "Workflow staticData changed")
            required |= {"state-idempotency"}
        if diff.get("pin_data_changed"):
            add_signal(signals, "PIN_DATA_CHANGED", "LOW", ["test-adequacy"], "Pinned data changed; ensure test evidence does not accidentally depend on editor state")

        settings = set(diff.get("settings_changed", []))
        if settings:
            required |= {"compatibility"}
        security_settings = settings & {"callerPolicy", "callerIds", "availableInMCP", "redactionPolicy"}
        if security_settings:
            add_signal(signals, "SECURITY_SETTING_CHANGED", "HIGH", ["security", "compatibility"], f"Security/reachability settings changed: {sorted(security_settings)}")
            required |= {"security"}
        if settings & {"executionOrder", "timezone"}:
            add_signal(signals, "EXECUTION_SEMANTICS_SETTING_CHANGED", "HIGH", ["n8n-semantics", "compatibility", "regression"], "Execution order or timezone changed")
        if "errorWorkflow" in settings:
            add_signal(signals, "ERROR_WORKFLOW_CHANGED", "MEDIUM", ["failure-recovery", "observability"], "Workflow errorWorkflow setting changed")
            required |= {"failure-recovery", "observability"}
        if "redactionPolicy" in settings:
            required |= {"observability", "test-adequacy"}

        for key in sorted(k for k in changed_keys if k in nodes):
            node = nodes[key]
            name = str(node.get("name") or key)
            stype = short_type(node)
            raw_type = str(node.get("type", ""))
            params = node.get("parameters") if isinstance(node.get("parameters"), dict) else {}
            changed_entry = next((x for x in diff.get("nodes", {}).get("modified", []) if x.get("key") == key), None)
            changed_fields = set(changed_entry.get("changed_fields", [])) if changed_entry else set()

            if node.get("credentials"):
                add_signal(signals, f"CREDENTIAL_SURFACE:{key}", "HIGH", ["integration", "security"], "Changed node uses credential references", name)
                required |= {"integration", "security"}
            if any(path.startswith("credentials") for path in changed_fields):
                add_signal(signals, f"CREDENTIAL_REFERENCE_CHANGED:{key}", "HIGH", ["integration", "security"], "Credential reference changed", name)
                required |= {"integration", "security"}

            if stype == "code" or "function" in stype:
                add_signal(signals, f"CODE_NODE_CHANGED:{key}", "MEDIUM", ["n8n-semantics", "security", "test-adequacy"], "Programmatic node changed", name)
                required |= {"security"}

            if "trigger" in stype or stype == "webhook":
                add_signal(signals, f"TRIGGER_CHANGED:{key}", "HIGH", ["integration", "security", "compatibility", "regression"], "Trigger/webhook behavior changed", name)
                required |= {"integration", "security", "compatibility"}

            if "executeworkflow" in stype or "subworkflow" in stype:
                add_signal(signals, f"SUBWORKFLOW_BOUNDARY_CHANGED:{key}", "HIGH", ["compatibility", "data-flow", "regression"], "Sub-workflow call boundary changed", name)
                required |= {"compatibility"}

            if any(token in stype for token in ("executecommand", "ssh", "readwritefile", "filesystem")):
                add_signal(signals, f"RISKY_EXECUTION_SURFACE:{key}", "HIGH", ["security", "integration"], "Changed node can execute commands or access host/filesystem resources", name)
                required |= {"security", "integration"}

            if any(token in stype for token in ("loopoveritems", "splitinbatches", "merge", "splitout", "aggregate", "summarize")):
                add_signal(signals, f"CARDINALITY_CONTROL_CHANGED:{key}", "MEDIUM", ["n8n-semantics", "performance", "regression"], "Changed node can alter cardinality, batching, or merge semantics", name)
                required |= {"performance"}

            if changed_entry and any(path == "typeVersion" or path.startswith("typeVersion") for path in changed_fields):
                add_signal(signals, f"TYPE_VERSION_CHANGED:{key}", "MEDIUM", ["compatibility", "regression"], "Node typeVersion changed", name)
                required |= {"compatibility"}

            retry_fields = ("retryOnFail", "maxTries", "waitBetweenTries", "onError", "continueOnFail")
            if changed_entry and any(any(path == field or path.startswith(field + ".") for field in retry_fields) for path in changed_fields):
                add_signal(signals, f"FAILURE_SEMANTICS_CHANGED:{key}", "HIGH", ["failure-recovery", "state-idempotency", "regression"], "Retry/error semantics changed", name)
                required |= {"failure-recovery", "state-idempotency"}

            if stype == "httprequest":
                required |= {"integration", "security"}
                method = str(params.get("method", "GET")).upper()
                if method in WRITE_HTTP_METHODS:
                    add_signal(signals, f"HTTP_WRITE_CHANGED:{key}", "HIGH", ["integration", "state-idempotency", "security", "observability"], f"HTTP Request uses {method}", name)
                    required |= {"state-idempotency", "observability"}
                else:
                    add_signal(signals, f"HTTP_IO_CHANGED:{key}", "MEDIUM", ["integration", "security"], f"HTTP Request uses {method}", name)

            query_text = " ".join(str(params.get(k, "")) for k in ("query", "queryString", "sql", "statement"))
            if query_text.strip():
                required |= {"integration"}
                if WRITE_SQL.search(query_text):
                    add_signal(signals, f"DATABASE_WRITE_CHANGED:{key}", "HIGH", ["integration", "state-idempotency", "security", "observability"], "Changed query appears to mutate database state", name)
                    required |= {"state-idempotency", "security", "observability"}

            if not is_local(node):
                add_signal(signals, f"EXTERNAL_OR_UNKNOWN_NODE_CHANGED:{key}", "MEDIUM", ["integration"], f"Changed node type {raw_type!r} is not classified as intrinsically local by the review harness", name)
                required |= {"integration"}

        removed = diff.get("nodes", {}).get("removed", [])
        if removed:
            add_signal(signals, "NODES_REMOVED", "MEDIUM", ["scope-diff", "regression", "compatibility"], f"{len(removed)} node(s) removed")
            required |= {"compatibility"}

        result = {
            "schema_version": 1,
            "candidate_behavior_sha256": diff.get("candidate_fingerprint", {}).get("behavior_sha256"),
            "behavioral_changed": bool(diff.get("behavioral_changed")),
            "required_lenses": sorted(required),
            "signals": signals,
        }
        write_json(result, args.out)
        print(f"required_lenses={len(result['required_lenses'])} signals={len(signals)}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
