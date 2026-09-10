#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from lab_preflight import validate_config
from n8n_api import client_from_config, load_lab_config
from trigger_webhook import verify_deployment

TERMINAL = {"success", "error", "canceled", "crashed"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def contains_exact(value, needle):
    if value == needle:
        return True
    if isinstance(value, dict):
        return any(contains_exact(v, needle) for v in value.values())
    if isinstance(value, list):
        return any(contains_exact(v, needle) for v in value)
    return False


def choose_candidate(client, candidate_ids, run_token, redact):
    if len(candidate_ids) == 1:
        return candidate_ids[0], None
    matches, details = [], {}
    for eid in candidate_ids:
        execution = client.get_execution(eid, include_data=True, redact=redact)
        details[eid] = execution
        if contains_exact(execution, run_token):
            matches.append(eid)
    if len(matches) == 1:
        return matches[0], details[matches[0]]
    if len(matches) > 1:
        raise RuntimeError(f"ambiguous execution correlation: run token appears in multiple new executions {matches}")
    raise RuntimeError("ambiguous execution correlation: multiple new executions appeared and run token did not uniquely identify one: " + ", ".join(candidate_ids))


def wait_for_execution(config_path, deployment_path, invocation_path, out_path):
    cfg = load_lab_config(config_path)
    errors, _ = validate_config(cfg)
    if errors:
        raise ValueError("lab preflight failed: " + "; ".join(errors))
    deployment = load_json(deployment_path)
    verify_deployment(cfg, deployment)
    invocation = load_json(invocation_path)
    if invocation.get("schema_version") != 1:
        raise ValueError("invocation schema_version must equal 1")
    if str(invocation.get("workflow_id")) != str(deployment["workflow_id"]):
        raise ValueError("invocation workflow id does not match deployment")
    run_token = invocation.get("run_token")
    if not run_token:
        raise ValueError("invocation has no run_token")

    client = client_from_config(config_path)
    preexisting = {str(x) for x in invocation.get("preexisting_execution_ids", [])}
    deadline = time.monotonic() + float(cfg.get("max_run_seconds", 180))
    poll = float(cfg.get("poll_interval_seconds", 1.5))
    redact = str(cfg.get("execution_data_mode", "follow"))
    if redact not in {"follow", "redact", "reveal"}:
        raise ValueError("execution_data_mode must be follow, redact, or reveal")
    selected_id = None
    last_detail = None

    while time.monotonic() < deadline:
        if selected_id is None:
            result = client.list_executions(workflow_id=str(deployment["workflow_id"]), limit=100, include_data=False)
            if not isinstance(result, dict) or not isinstance(result.get("data"), list):
                raise ValueError("unexpected execution-list response while correlating run")
            new_ids = [str(x.get("id")) for x in result["data"] if isinstance(x, dict) and x.get("id") and str(x.get("id")) not in preexisting]
            if new_ids:
                selected_id, prefetched = choose_candidate(client, new_ids, run_token, redact)
                last_detail = prefetched
        if selected_id is not None:
            if last_detail is None:
                last_detail = client.get_execution(selected_id, include_data=True, redact=redact)
            status = str(last_detail.get("status", "unknown"))
            if status in TERMINAL:
                if last_detail.get("dataTooLargeToDisplay"):
                    raise RuntimeError(f"execution {selected_id} completed but detailed data was omitted because it exceeded the n8n display limit")
                redaction = (((last_detail.get("data") or {}).get("redactionInfo") or {}).get("isRedacted"))
                last_detail.setdefault("_lab_capture", {})
                last_detail["_lab_capture"].update({"correlated_run_token": run_token, "fixture_id": invocation.get("fixture_id"), "fixture_sha256": invocation.get("fixture_sha256")})
                if redaction:
                    last_detail["_lab_capture"]["warning"] = "execution data is redacted; data-level assertions may be impossible"
                dump_json(last_detail, out_path)
                return last_detail
            time.sleep(poll)
            last_detail = client.get_execution(selected_id, include_data=True, redact=redact)
        else:
            time.sleep(poll)

    if last_detail is not None:
        partial = dict(last_detail)
        partial.setdefault("_lab_capture", {})["timeout"] = True
        dump_json(partial, out_path)
    raise TimeoutError(f"no terminal execution correlated within max_run_seconds={cfg.get('max_run_seconds', 180)}" + (f"; selected execution={selected_id}" if selected_id else ""))


def main():
    p = argparse.ArgumentParser(description="Correlate and capture the n8n execution created by one lab webhook invocation")
    p.add_argument("--config", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--invocation", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    try:
        execution = wait_for_execution(args.config, args.deployment, args.invocation, args.out)
        print(f"PASS: captured execution id={execution.get('id')} status={execution.get('status')}")
        return 0
    except TimeoutError as exc:
        print(f"TIMEOUT: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
