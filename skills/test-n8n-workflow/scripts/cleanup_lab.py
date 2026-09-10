#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from deploy_lab_clone import workflow_semantic_hash
from lab_preflight import validate_config
from n8n_api import N8NAPIError, client_from_config, load_lab_config
from trigger_webhook import verify_deployment


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path=None):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def cleanup(config_path, deployment_path, out_path=None):
    cfg = load_lab_config(config_path)
    errors, _ = validate_config(cfg)
    if errors:
        raise ValueError("lab preflight failed: " + "; ".join(errors))
    deployment = load_json(deployment_path)
    verify_deployment(cfg, deployment)
    client = client_from_config(config_path)
    workflow_id = str(deployment["workflow_id"])
    expected_name = str(deployment["workflow_name"])
    prefix = cfg.get("workflow_name_prefix", "LAB__")
    result = {
        "schema_version": 1, "workflow_id": workflow_id, "workflow_name": expected_name,
        "attempted_at": datetime.now(timezone.utc).isoformat(), "identity_verified": False,
        "unpublish": None, "delete": None, "absent_after_cleanup": False,
    }
    try:
        workflow = client.get_workflow(workflow_id)
    except N8NAPIError as exc:
        if exc.status == 404:
            result.update({"identity_verified": True, "unpublish": "NOT_NEEDED_ALREADY_ABSENT", "delete": "NOT_NEEDED_ALREADY_ABSENT", "absent_after_cleanup": True})
            dump_json(result, out_path)
            return result
        raise
    current_name = workflow.get("name") if isinstance(workflow, dict) else None
    if current_name != expected_name or not str(current_name or "").startswith(prefix):
        raise RuntimeError(f"REFUSED cleanup: fetched workflow identity mismatch id={workflow_id!r} expected_name={expected_name!r} actual_name={current_name!r}")
    expected_hash = deployment.get("workflow_semantic_sha256")
    if expected_hash and workflow_semantic_hash(workflow) != expected_hash:
        raise RuntimeError("REFUSED cleanup: lab workflow content has drifted since deployment")
    result["identity_verified"] = True
    try:
        client.unpublish_workflow(workflow_id)
        result["unpublish"] = "OK"
    except N8NAPIError as exc:
        if exc.status in {400, 404, 409}:
            result["unpublish"] = f"NON_FATAL_HTTP_{exc.status}"
        else:
            raise
    try:
        client.delete_workflow(workflow_id)
        result["delete"] = "OK"
    except N8NAPIError as exc:
        if exc.status == 404:
            result["delete"] = "ALREADY_ABSENT"
        else:
            raise
    try:
        client.get_workflow(workflow_id)
    except N8NAPIError as exc:
        if exc.status == 404:
            result["absent_after_cleanup"] = True
        else:
            raise
    if not result["absent_after_cleanup"]:
        raise RuntimeError("cleanup verification failed: workflow still exists after delete")
    dump_json(result, out_path)
    return result


def main():
    p = argparse.ArgumentParser(description="Safely unpublish/delete an ephemeral n8n lab workflow")
    p.add_argument("--config", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--out")
    args = p.parse_args()
    try:
        result = cleanup(args.config, args.deployment, args.out)
        print(f"PASS: cleanup workflow={result['workflow_id']} absent={result['absent_after_cleanup']}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
