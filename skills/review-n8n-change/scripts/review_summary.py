#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact summary of an n8n change review directory")
    parser.add_argument("review_dir")
    args = parser.parse_args()
    root = Path(args.review_dir).resolve()
    verdict_path = root / "verdict.json"
    findings_path = root / "findings.json"
    coverage_path = root / "coverage.json"
    risk_path = root / "risk-scan.json"

    verdict = load_json(verdict_path) if verdict_path.is_file() else {}
    findings = load_json(findings_path) if findings_path.is_file() else {"findings": []}
    coverage = load_json(coverage_path) if coverage_path.is_file() else {}
    risk = load_json(risk_path) if risk_path.is_file() else {}

    print(f"Verdict: {verdict.get('verdict', 'NOT_GATED')}")
    fp = verdict.get("candidate_behavior_sha256") or coverage.get("candidate_behavior_sha256")
    if fp:
        print(f"Candidate: {fp}")
    rows = [f for f in findings.get("findings", []) if isinstance(f, dict)]
    open_rows = [f for f in rows if f.get("status") in {"OPEN", "NEEDS_EVIDENCE", "ACCEPTED_RISK"}]
    print(f"Findings: {len(rows)} total; {len(open_rows)} unresolved/conditional")
    if risk.get("required_lenses"):
        reviewed = {x.get("id") for x in coverage.get("lenses", []) if isinstance(x, dict) and x.get("status") in {"REVIEWED", "NOT_APPLICABLE"}}
        required = set(risk.get("required_lenses", []))
        print(f"Review lenses: {len(reviewed & required)}/{len(required)} complete")
    for key, label in (("blockers", "Blockers"), ("evidence_gaps", "Evidence gaps"), ("conditions", "Conditions"), ("residual_risks", "Residual risks")):
        values = verdict.get(key, [])
        if values:
            print(f"{label}:")
            for value in values:
                print(f"- {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
