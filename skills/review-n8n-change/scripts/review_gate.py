#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import load_json, resolve_path, workflow_fingerprints, write_json
from validate_findings import validate as validate_findings
from validate_coverage import validate as validate_coverage
from validate_review_packet import validate as validate_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute a deterministic release-readiness verdict for an n8n change review")
    parser.add_argument("--packet", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--risk", required=True)
    parser.add_argument("--findings", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--bound-evidence", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        packet_errors = validate_packet(args.packet)
        packet = load_json(args.packet)
        diff = load_json(args.diff)
        risk = load_json(args.risk)
        findings = load_json(args.findings)
        coverage = load_json(args.coverage)
        bound = load_json(args.bound_evidence)

        req_path = resolve_path(args.packet, packet.get("requirements"))
        if not req_path:
            raise ValueError("review packet has no requirements path")
        finding_errors = validate_findings(args.findings)
        coverage_errors = validate_coverage(str(req_path), args.risk, args.coverage, args.bound_evidence)

        blockers: list[str] = []
        gaps: list[str] = []
        conditions: list[str] = []
        residual: list[str] = []

        if packet_errors:
            gaps.extend(f"packet: {e}" for e in packet_errors)
        if finding_errors:
            gaps.extend(f"findings: {e}" for e in finding_errors)
        if coverage_errors:
            gaps.extend(f"coverage: {e}" for e in coverage_errors)

        candidate_path = resolve_path(args.packet, packet.get("candidate_workflow"))
        if not candidate_path or not candidate_path.is_file():
            gaps.append("candidate workflow cannot be resolved")
            candidate_fp = None
        else:
            candidate_fp = workflow_fingerprints(load_json(candidate_path))["behavior_sha256"]

        for label, data in (("packet", packet), ("diff", diff.get("candidate_fingerprint", {})), ("risk", risk), ("findings", findings), ("coverage", coverage), ("bound evidence", bound)):
            value = data.get("candidate_behavior_sha256") if isinstance(data, dict) else None
            if label == "diff" and isinstance(data, dict):
                value = data.get("behavior_sha256")
            if value and candidate_fp and value != candidate_fp:
                gaps.append(f"{label} candidate fingerprint does not match reviewed candidate")

        tests = [t for t in bound.get("tests", []) if isinstance(t, dict)]
        if any(t.get("state") == "BOUND_FAIL" for t in tests):
            failed = [str(t.get("id")) for t in tests if t.get("state") == "BOUND_FAIL"]
            blockers.append(f"bound runtime test failure(s): {', '.join(failed)}")
        if diff.get("behavioral_changed") and not any(t.get("state") == "BOUND_PASS" for t in tests):
            gaps.append("behavioral change has no BOUND_PASS runtime evidence")

        for section_name in ("acceptance", "invariants"):
            for entry in coverage.get(section_name, []) if isinstance(coverage.get(section_name), list) else []:
                if not isinstance(entry, dict):
                    continue
                eid = str(entry.get("id"))
                status = entry.get("status")
                if status == "CONTRADICTED":
                    blockers.append(f"{section_name} {eid} is contradicted")
                elif status == "NOT_VERIFIED":
                    gaps.append(f"{section_name} {eid} is not verified")

        lens_map = {e.get("id"): e for e in coverage.get("lenses", []) if isinstance(e, dict) and isinstance(e.get("id"), str)}
        for lens in risk.get("required_lenses", []):
            entry = lens_map.get(lens)
            if not entry:
                gaps.append(f"required review lens {lens} missing")
            elif entry.get("status") == "NOT_REVIEWED":
                gaps.append(f"required review lens {lens} not reviewed")

        for finding in findings.get("findings", []) if isinstance(findings.get("findings"), list) else []:
            if not isinstance(finding, dict):
                continue
            fid = str(finding.get("id"))
            severity = finding.get("severity")
            status = finding.get("status")
            claim = str(finding.get("claim", "")).strip()
            if status == "OPEN":
                if severity in {"CRITICAL", "HIGH"}:
                    blockers.append(f"{fid} {severity}: {claim}")
                elif severity == "MEDIUM":
                    conditions.append(f"{fid} MEDIUM: {claim}")
                elif severity in {"LOW", "INFO"}:
                    residual.append(f"{fid} {severity}: {claim}")
            elif status == "NEEDS_EVIDENCE":
                if severity in {"CRITICAL", "HIGH"}:
                    gaps.append(f"{fid} {severity} needs evidence: {claim}")
                elif severity == "MEDIUM":
                    conditions.append(f"{fid} MEDIUM needs evidence: {claim}")
                else:
                    residual.append(f"{fid} {severity} needs evidence: {claim}")
            elif status == "ACCEPTED_RISK":
                conditions.append(f"{fid} accepted risk ({severity}): {claim}")

        # Deduplicate while preserving order.
        def uniq(values: list[str]) -> list[str]:
            return list(dict.fromkeys(values))
        blockers, gaps, conditions, residual = map(uniq, (blockers, gaps, conditions, residual))

        if blockers:
            verdict = "REJECT"
        elif gaps:
            verdict = "INSUFFICIENT_EVIDENCE"
        elif conditions:
            verdict = "PASS_WITH_CONDITIONS"
        else:
            verdict = "PASS"

        result = {
            "schema_version": 1,
            "candidate_behavior_sha256": candidate_fp,
            "verdict": verdict,
            "blockers": blockers,
            "conditions": conditions,
            "evidence_gaps": gaps,
            "residual_risks": residual,
        }
        write_json(result, args.out)
        print(verdict)
        return 0 if verdict in {"PASS", "PASS_WITH_CONDITIONS"} else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
