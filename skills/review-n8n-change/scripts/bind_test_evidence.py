#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import load_json, resolve_path, workflow_fingerprints, write_json


def interpret_summary(summary: dict[str, Any]) -> tuple[bool | None, str | None]:
    passed = summary.get("passed")
    if not isinstance(passed, bool):
        return None, "summary has no boolean passed field"
    counts = summary.get("counts")
    if isinstance(counts, dict) and isinstance(counts.get("executed"), int) and counts.get("executed") == 0:
        return None, "summary reports zero executed cases"
    return passed, None


def bind(candidate_path: str, manifest_path: str) -> dict[str, Any]:
    candidate = load_json(candidate_path)
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be a JSON object")
    candidate_fp = workflow_fingerprints(candidate)["behavior_sha256"]
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("tests"), list):
        raise ValueError("test evidence manifest must have schema_version=1 and tests array")

    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for entry in manifest["tests"]:
        if not isinstance(entry, dict):
            raise ValueError("test evidence entries must be objects")
        tid = entry.get("id")
        if not isinstance(tid, str) or not tid.strip() or tid in seen:
            raise ValueError("test evidence IDs must be unique non-empty strings")
        seen.add(tid)
        row: dict[str, Any] = {
            "id": tid,
            "supports": entry.get("supports", []),
            "state": "UNREADABLE",
            "candidate_behavior_sha256": candidate_fp,
            "test_source_behavior_sha256": None,
            "strategy": None,
            "passed": None,
            "reason": None,
        }
        try:
            plan_path = resolve_path(manifest_path, entry.get("test_plan"))
            summary_path = resolve_path(manifest_path, entry.get("summary"))
            if not plan_path or not plan_path.is_file():
                raise ValueError("test_plan not found")
            if not summary_path or not summary_path.is_file():
                raise ValueError("summary not found")
            plan = load_json(plan_path)
            summary = load_json(summary_path)
            if not isinstance(plan, dict) or plan.get("schema_version") != 1:
                raise ValueError("test_plan must have schema_version=1")
            if not isinstance(summary, dict) or summary.get("schema_version") != 1:
                raise ValueError("summary must have schema_version=1")
            strategy = plan.get("strategy")
            row["strategy"] = strategy
            source = plan.get("source") if isinstance(plan.get("source"), dict) else {}
            source_path = source.get("workflow_snapshot")
            source_snapshot = resolve_path(plan_path, source_path) if source_path else None
            if not source_snapshot or not source_snapshot.is_file():
                raise ValueError("test_plan source.workflow_snapshot cannot be resolved")
            source_wf = load_json(source_snapshot)
            source_fp = workflow_fingerprints(source_wf)["behavior_sha256"]
            row["test_source_behavior_sha256"] = source_fp
            passed, summary_error = interpret_summary(summary)
            row["passed"] = passed
            if source_fp != candidate_fp:
                row["state"] = "STALE"
                row["reason"] = "test source behavioral fingerprint differs from reviewed candidate"
            elif strategy == "SNAPSHOT_ONLY" or summary_error:
                row["state"] = "NOT_RUNTIME"
                row["reason"] = summary_error or "snapshot-only evidence did not execute candidate behavior"
            elif passed is True:
                row["state"] = "BOUND_PASS"
            elif passed is False:
                row["state"] = "BOUND_FAIL"
        except Exception as exc:
            row["state"] = "UNREADABLE"
            row["reason"] = str(exc)
        results.append(row)

    return {
        "schema_version": 1,
        "candidate_behavior_sha256": candidate_fp,
        "tests": results,
        "counts": {
            "total": len(results),
            "bound_pass": sum(1 for r in results if r["state"] == "BOUND_PASS"),
            "bound_fail": sum(1 for r in results if r["state"] == "BOUND_FAIL"),
            "stale": sum(1 for r in results if r["state"] == "STALE"),
            "unusable": sum(1 for r in results if r["state"] in {"UNREADABLE", "NOT_RUNTIME"}),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind test results to the exact reviewed n8n candidate")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = bind(args.candidate, args.manifest)
        write_json(result, args.out)
        print(" ".join(f"{k}={v}" for k, v in result["counts"].items()))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
