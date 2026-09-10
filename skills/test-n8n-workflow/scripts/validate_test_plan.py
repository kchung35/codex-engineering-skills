#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from n8n_api import load_lab_config

STRATEGIES = {"BOUNDARY_REPLAY", "RETRY_IN_LAB", "NATIVE_TRIGGER_LAB", "SNAPSHOT_ONLY"}
CLEANUP = {"DELETE", "KEEP_FOR_INSPECTION"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_plan(cfg, plan):
    errors, warnings = [], []
    if not isinstance(plan, dict):
        return ["test plan must be a JSON object"], warnings
    if plan.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    for key in ("test_id", "question"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            errors.append(f"{key} must be a non-empty string")
    strategy = plan.get("strategy")
    if strategy not in STRATEGIES:
        errors.append(f"strategy must be one of {sorted(STRATEGIES)}")
    cleanup = plan.get("cleanup_policy")
    if cleanup not in CLEANUP:
        errors.append(f"cleanup_policy must be one of {sorted(CLEANUP)}")
    timeout = plan.get("timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        errors.append("timeout_seconds must be positive")
    elif timeout > float(cfg.get("max_run_seconds", 180)):
        errors.append("timeout_seconds exceeds lab max_run_seconds")

    cases = plan.get("cases")
    if cases is not None:
        if not isinstance(cases, list):
            errors.append("cases must be an array when present")
            cases = []
        else:
            ids = []
            for i, case in enumerate(cases):
                if not isinstance(case, dict):
                    errors.append(f"cases[{i}] must be an object")
                    continue
                cid = case.get("id")
                if not isinstance(cid, str) or not cid.strip():
                    errors.append(f"cases[{i}].id must be a non-empty string")
                else:
                    ids.append(cid)
                for key in ("fixture", "assertions"):
                    if not isinstance(case.get(key), str) or not case[key].strip():
                        errors.append(f"cases[{i}].{key} must be a non-empty path string")
            if len(ids) != len(set(ids)):
                errors.append("case ids must be unique")
            if len(cases) > int(cfg.get("max_cases_per_matrix", 25)):
                errors.append("case count exceeds lab max_cases_per_matrix")

    if strategy == "BOUNDARY_REPLAY":
        source = plan.get("source")
        if not isinstance(source, dict) or not isinstance(source.get("workflow_snapshot"), str) or not source.get("workflow_snapshot"):
            errors.append("BOUNDARY_REPLAY requires source.workflow_snapshot")
        boundary = plan.get("boundary")
        if not isinstance(boundary, dict) or not isinstance(boundary.get("node"), str) or not boundary.get("node"):
            errors.append("BOUNDARY_REPLAY requires boundary.node")
        else:
            if boundary.get("connection_type", "main") != "main":
                errors.append("BOUNDARY_REPLAY currently supports boundary.connection_type=main only")
            oi = boundary.get("output_index", 0)
            if not isinstance(oi, int) or oi < 0:
                errors.append("boundary.output_index must be a non-negative integer")
        if not isinstance(cases, list) or not cases:
            errors.append("BOUNDARY_REPLAY requires at least one case")
        if not isinstance(plan.get("side_effect_manifest"), str) or not plan.get("side_effect_manifest"):
            errors.append("BOUNDARY_REPLAY requires side_effect_manifest")
        if cfg.get("credential_reference_policy") == "REQUIRE_MAP" and not plan.get("credential_map"):
            warnings.append("credential_reference_policy=REQUIRE_MAP: credential_map omitted; compilation is valid only if retained nodes use no credentials")
    elif strategy == "RETRY_IN_LAB":
        if not str(plan.get("execution_id") or "").strip():
            errors.append("RETRY_IN_LAB requires execution_id")
        if not isinstance(plan.get("side_effect_manifest"), str) or not plan.get("side_effect_manifest"):
            errors.append("RETRY_IN_LAB requires side_effect_manifest")
    elif strategy == "NATIVE_TRIGGER_LAB":
        if not str(plan.get("adapter") or "").strip():
            errors.append("NATIVE_TRIGGER_LAB requires adapter/runbook identifier")
        if not isinstance(plan.get("side_effect_manifest"), str) or not plan.get("side_effect_manifest"):
            errors.append("NATIVE_TRIGGER_LAB requires side_effect_manifest")
        if not isinstance(cases, list) or not cases:
            errors.append("NATIVE_TRIGGER_LAB requires at least one deterministic case")
    elif strategy == "SNAPSHOT_ONLY":
        source = plan.get("source")
        if not isinstance(source, dict) or not any(source.get(k) for k in ("workflow_id", "execution_id", "workflow_snapshot", "execution_snapshot")):
            errors.append("SNAPSHOT_ONLY requires at least one source workflow/execution identifier or snapshot")
        if cases:
            warnings.append("SNAPSHOT_ONLY ignores executable fixture cases")
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description="Validate an n8n laboratory test plan before execution")
    p.add_argument("--config", required=True)
    p.add_argument("--plan", required=True)
    args = p.parse_args()
    try:
        cfg = load_lab_config(args.config)
        plan = load_json(args.plan)
        errors, warnings = validate_plan(cfg, plan)
        for w in warnings:
            print(f"WARN: {w}")
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            return 2
        print(f"PASS: test plan {plan['test_id']} strategy={plan['strategy']}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
