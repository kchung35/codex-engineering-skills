#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from common import load_json

SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
STATUSES = {"OPEN", "NEEDS_EVIDENCE", "RESOLVED", "ACCEPTED_RISK", "FALSE_POSITIVE"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


def validate(path: str) -> list[str]:
    data = load_json(path)
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("findings"), list):
        return ["findings must be an object with schema_version=1 and findings array"]
    errors: list[str] = []
    ids: set[str] = set()
    for i, finding in enumerate(data["findings"]):
        label = f"finding[{i}]"
        if not isinstance(finding, dict):
            errors.append(f"{label} must be an object")
            continue
        fid = finding.get("id")
        if not isinstance(fid, str) or not fid.strip():
            errors.append(f"{label}.id must be non-empty")
        elif fid in ids:
            errors.append(f"duplicate finding id {fid}")
        else:
            ids.add(fid)
        if finding.get("severity") not in SEVERITIES:
            errors.append(f"{label}.severity invalid")
        if finding.get("status") not in STATUSES:
            errors.append(f"{label}.status invalid")
        if finding.get("confidence") not in CONFIDENCE:
            errors.append(f"{label}.confidence invalid")
        for key in ("category", "claim", "failure_scenario", "impact", "required_action", "verification_needed"):
            if not isinstance(finding.get(key), str) or not finding[key].strip():
                errors.append(f"{label}.{key} must be a non-empty string")
        evidence = finding.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{label}.evidence must be an array")
            evidence = []
        if finding.get("status") == "OPEN" and not evidence:
            errors.append(f"{label} OPEN finding requires evidence")
        if finding.get("status") in {"RESOLVED", "FALSE_POSITIVE"}:
            resolution = finding.get("resolution_evidence")
            if not isinstance(resolution, list) or not resolution:
                errors.append(f"{label} {finding.get('status')} requires resolution_evidence")
        for key in ("affected_requirements", "affected_invariants"):
            if key in finding and not isinstance(finding.get(key), list):
                errors.append(f"{label}.{key} must be an array")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate structured n8n review findings")
    parser.add_argument("findings")
    args = parser.parse_args()
    try:
        errors = validate(args.findings)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("PASS: findings valid")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
