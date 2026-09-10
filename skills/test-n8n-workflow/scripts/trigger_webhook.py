#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from deploy_lab_clone import workflow_semantic_hash
from lab_preflight import validate_config
from n8n_api import client_from_config, load_lab_config, normalize_instance_base_url
from validate_fixture import digest_items, validate_fixture


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify_deployment(cfg, deployment):
    if deployment.get("schema_version") != 1:
        raise ValueError("deployment receipt schema_version must equal 1")
    if deployment.get("environment_class") != "NON_PRODUCTION":
        raise ValueError("deployment receipt is not NON_PRODUCTION")
    if normalize_instance_base_url(deployment.get("instance_base_url", "")) != normalize_instance_base_url(cfg["instance_base_url"]):
        raise ValueError("deployment instance does not match current lab config")
    prefix = cfg.get("workflow_name_prefix", "LAB__")
    if not str(deployment.get("workflow_name", "")).startswith(prefix):
        raise ValueError("deployment workflow name does not satisfy lab prefix")
    if not deployment.get("workflow_id") or not deployment.get("webhook_path"):
        raise ValueError("deployment receipt lacks workflow_id or webhook_path")


def webhook_headers_from_env(cfg):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}
    mapping = cfg.get("webhook_headers_from_env") or {}
    if mapping and not isinstance(mapping, dict):
        raise ValueError("webhook_headers_from_env must be an object")
    for header, env_name in mapping.items():
        if not isinstance(header, str) or not isinstance(env_name, str):
            raise ValueError("webhook_headers_from_env entries must map strings to environment variable names")
        value = os.getenv(env_name)
        if value is None:
            raise ValueError(f"required webhook header environment variable {env_name!r} is not set")
        headers[header] = value
    return headers


def trigger(config_path, deployment_path, fixture_path, out_path):
    cfg = load_lab_config(config_path)
    errors, _ = validate_config(cfg)
    if errors:
        raise ValueError("lab preflight failed: " + "; ".join(errors))
    deployment = load_json(deployment_path)
    verify_deployment(cfg, deployment)
    fixture = load_json(fixture_path)
    fixture_errors, warnings = validate_fixture(fixture, int(cfg.get("max_fixture_bytes", 1048576)))
    if fixture_errors:
        raise ValueError("fixture validation failed: " + "; ".join(fixture_errors))
    boundary = deployment.get("boundary") or {}
    fixture_meta = fixture.get("metadata") or {}
    if boundary.get("node") and fixture_meta.get("boundary_node") != boundary.get("node"):
        raise ValueError("fixture boundary_node does not match deployed replay boundary")
    if boundary.get("output_index") is not None and int(fixture_meta.get("output_index", 0)) != int(boundary.get("output_index")):
        raise ValueError("fixture output_index does not match deployed replay boundary")

    client = client_from_config(config_path)
    current = client.get_workflow(str(deployment["workflow_id"]))
    if not isinstance(current, dict) or current.get("name") != deployment.get("workflow_name"):
        raise ValueError("deployed workflow identity could not be re-verified before trigger")
    expected_hash = deployment.get("workflow_semantic_sha256")
    if expected_hash and workflow_semantic_hash(current) != expected_hash:
        raise ValueError("deployed lab workflow has drifted since deployment; refusing to execute")
    before = client.list_executions(workflow_id=str(deployment["workflow_id"]), limit=100, include_data=False)
    if not isinstance(before, dict) or not isinstance(before.get("data"), list):
        raise ValueError("unexpected execution-list response before trigger")
    preexisting_ids = [str(x.get("id")) for x in before["data"] if isinstance(x, dict) and x.get("id")]

    fixture_sha = digest_items(fixture["items"])
    run_token = uuid.uuid4().hex
    body = {"items": fixture["items"], "_lab": {"run_token": run_token, "fixture_id": fixture["metadata"]["fixture_id"], "fixture_sha256": fixture_sha}}
    path = urllib.parse.quote(str(deployment["webhook_path"]).lstrip("/"), safe="/")
    url = str(deployment.get("webhook_base_url") or cfg["webhook_base_url"]).rstrip("/") + "/webhook/" + path
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    started_at = datetime.now(timezone.utc).isoformat()
    req = urllib.request.Request(url, data=payload, method="POST", headers=webhook_headers_from_env(cfg))
    try:
        with urllib.request.urlopen(req, timeout=float(cfg.get("webhook_timeout_seconds", 30))) as resp:
            raw = resp.read(int(cfg.get("max_webhook_response_bytes", 65536)) + 1)
            if len(raw) > int(cfg.get("max_webhook_response_bytes", 65536)):
                raise ValueError("webhook response exceeded configured max_webhook_response_bytes")
            status = int(resp.status)
            response_text = raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read(4096)
        raise RuntimeError(f"webhook POST returned HTTP {exc.code}: {raw.decode('utf-8', errors='replace')[:2000]}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"webhook POST transport failure: {exc.reason}") from None

    invocation = {
        "schema_version": 1, "workflow_id": str(deployment["workflow_id"]), "workflow_name": deployment["workflow_name"],
        "case_id": deployment.get("case_id"), "fixture_id": fixture["metadata"]["fixture_id"], "fixture_sha256": fixture_sha,
        "run_token": run_token, "started_at": started_at, "webhook_http_status": status,
        "webhook_response": response_text[: int(cfg.get("max_webhook_response_bytes", 65536))],
        "preexisting_execution_ids": preexisting_ids, "warnings": warnings,
    }
    dump_json(invocation, out_path)
    return invocation


def main():
    p = argparse.ArgumentParser(description="Trigger one fixture against an ephemeral published lab webhook")
    p.add_argument("--config", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--fixture", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    try:
        inv = trigger(args.config, args.deployment, args.fixture, args.out)
        print(f"PASS: webhook accepted fixture={inv['fixture_id']} http={inv['webhook_http_status']} run_token={inv['run_token']}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
