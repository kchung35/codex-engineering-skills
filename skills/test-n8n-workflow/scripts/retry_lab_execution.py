#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from deploy_lab_clone import workflow_semantic_hash
from lab_preflight import validate_config
from n8n_api import client_from_config, load_lab_config
from validate_lab_workflow import validate_workflow


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def retry(config_path, execution_id, side_effects_path, out_path, execution_out_path, *, ack_writes=False):
    cfg = load_lab_config(config_path)
    errors, _ = validate_config(cfg)
    if errors:
        raise ValueError("lab preflight failed: " + "; ".join(errors))
    client = client_from_config(config_path)
    original = client.get_execution(str(execution_id), include_data=False)
    workflow_id = str(original.get("workflowId") or "")
    if not workflow_id:
        raise ValueError("execution response has no workflowId")
    workflow = client.get_workflow(workflow_id)
    prefix = cfg.get("workflow_name_prefix", "LAB__")
    if not str(workflow.get("name", "")).startswith(prefix):
        raise ValueError("RETRY_IN_LAB is restricted to workflows with the configured lab prefix")
    if cfg.get("project_id") and not workflow.get("projectId"):
        workflow = dict(workflow)
        workflow["projectId"] = cfg["project_id"]
    manifest = load_json(side_effects_path)
    safety_errors, warnings, report = validate_workflow(cfg, workflow, manifest, ack_writes=ack_writes)
    if safety_errors:
        raise ValueError("retry safety gate failed: " + "; ".join(safety_errors))

    result = client.retry_execution(str(execution_id), load_workflow=True)
    if not isinstance(result, dict) or not result.get("id"):
        raise ValueError("retry endpoint returned no new execution id")
    receipt = {
        "schema_version": 1, "strategy": "RETRY_IN_LAB", "source_execution_id": str(execution_id),
        "new_execution_id": str(result["id"]), "workflow_id": workflow_id, "workflow_name": workflow.get("name"),
        "validated_workflow_semantic_sha256": workflow_semantic_hash(workflow), "loadWorkflow": True,
        "side_effect_classifications": report, "warnings": warnings,
        "status_from_retry_response": result.get("status"), "capture_status": "PENDING",
    }
    dump_json(receipt, out_path)

    new_id = str(result["id"])
    deadline = time.monotonic() + float(cfg.get("max_run_seconds", 180))
    poll = float(cfg.get("poll_interval_seconds", 1.5))
    redact = str(cfg.get("execution_data_mode", "follow"))
    last = None
    terminal = {"success", "error", "canceled", "crashed"}
    while time.monotonic() < deadline:
        last = client.get_execution(new_id, include_data=True, redact=redact)
        if str(last.get("status")) in terminal:
            if last.get("dataTooLargeToDisplay"):
                dump_json(last, execution_out_path)
                receipt["capture_status"] = "INSUFFICIENT_OVERSIZED_DATA"
                receipt["final_status"] = last.get("status")
                dump_json(receipt, out_path)
                raise RuntimeError("retry completed but detailed execution data exceeded n8n display limit")
            dump_json(last, execution_out_path)
            receipt["capture_status"] = "CAPTURED"
            receipt["final_status"] = last.get("status")
            dump_json(receipt, out_path)
            return receipt
        time.sleep(poll)
    if last is not None:
        dump_json(last, execution_out_path)
    receipt["capture_status"] = "TIMEOUT"
    dump_json(receipt, out_path)
    raise TimeoutError(f"retry execution {new_id} did not reach terminal state within configured max_run_seconds")


def main():
    p = argparse.ArgumentParser(description="Safely retry an execution only on a validated non-production lab workflow")
    p.add_argument("--config", required=True)
    p.add_argument("--execution-id", required=True)
    p.add_argument("--side-effects", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--execution-out", required=True)
    p.add_argument("--ack-writes", action="store_true")
    args = p.parse_args()
    try:
        receipt = retry(args.config, args.execution_id, args.side_effects, args.out, args.execution_out, ack_writes=args.ack_writes)
        print(f"PASS: retry captured new_execution_id={receipt['new_execution_id']} status={receipt.get('final_status')}")
        return 0
    except TimeoutError as exc:
        print(f"TIMEOUT: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
