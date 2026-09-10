#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from typing import Any

from common import load_json

COVERAGE_STATUSES = {"VERIFIED", "CONTRADICTED", "NOT_VERIFIED", "NOT_APPLICABLE"}
LENS_STATUSES = {"REVIEWED", "NOT_REVIEWED", "NOT_APPLICABLE"}


def requirement_ids(requirements: dict[str, Any]) -> tuple[list[str], list[tuple[str, str]]]:
    acceptance_ids: list[str] = []
    for i, item in enumerate(requirements.get("acceptance", []) or [], start=1):
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
            acceptance_ids.append(item["id"])
        else:
            acceptance_ids.append(f"A{i}")
    invariants: list[tuple[str, str]] = []
    for i, item in enumerate(requirements.get("invariants", []) or [], start=1):
        if isinstance(item, dict):
            iid = item.get("id") if isinstance(item.get("id"), str) and item.get("id").strip() else f"I{i}"
            statement = str(item.get("statement", ""))
        else:
            iid = f"I{i}"
            statement = str(item)
        invariants.append((iid, statement))
    return acceptance_ids, invariants


def validate(requirements_path: str, risk_path: str, coverage_path: str, bound_evidence_path: str) -> list[str]:
    requirements = load_json(requirements_path)
    risk = load_json(risk_path)
    coverage = load_json(coverage_path)
    bound = load_json(bound_evidence_path)
    errors: list[str] = []
    for name, data in (("requirements", requirements), ("risk", risk), ("coverage", coverage), ("bound evidence", bound)):
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return [f"{name} must have schema_version=1"]

    req_acceptance, req_invariants = requirement_ids(requirements)
    cov_acceptance = coverage.get("acceptance") if isinstance(coverage.get("acceptance"), list) else []
    cov_invariants = coverage.get("invariants") if isinstance(coverage.get("invariants"), list) else []
    cov_lenses = coverage.get("lenses") if isinstance(coverage.get("lenses"), list) else []

    candidate_hashes = {
        risk.get("candidate_behavior_sha256"),
        coverage.get("candidate_behavior_sha256"),
        bound.get("candidate_behavior_sha256"),
    }
    candidate_hashes.discard(None)
    if len(candidate_hashes) > 1:
        errors.append("risk/coverage/bound-evidence candidate fingerprints do not match")

    def map_entries(entries: list[Any], label: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"{label}[{i}] must be an object")
                continue
            eid = entry.get("id")
            if not isinstance(eid, str) or not eid.strip():
                errors.append(f"{label}[{i}].id must be non-empty")
                continue
            if eid in result:
                errors.append(f"duplicate {label} id {eid}")
            result[eid] = entry
        return result

    amap = map_entries(cov_acceptance, "acceptance")
    imap = map_entries(cov_invariants, "invariants")
    lmap = map_entries(cov_lenses, "lenses")

    for aid in req_acceptance:
        if aid not in amap:
            errors.append(f"missing acceptance coverage for {aid}")
    for iid, _ in req_invariants:
        if iid not in imap:
            errors.append(f"missing invariant coverage for {iid}")

    usable_test_ids = {t.get("id") for t in bound.get("tests", []) if isinstance(t, dict) and t.get("state") == "BOUND_PASS"}
    known_test_ids = {t.get("id") for t in bound.get("tests", []) if isinstance(t, dict)}
    support_map = {t.get("id"): set(t.get("supports", [])) for t in bound.get("tests", []) if isinstance(t, dict)}

    for label, entries in (("acceptance", amap), ("invariant", imap)):
        for eid, entry in entries.items():
            status = entry.get("status")
            if status not in COVERAGE_STATUSES:
                errors.append(f"{label} {eid} has invalid status")
            evidence = entry.get("evidence_ids", [])
            if not isinstance(evidence, list):
                errors.append(f"{label} {eid}.evidence_ids must be an array")
                evidence = []
            if status == "VERIFIED" and not evidence:
                errors.append(f"{label} {eid} VERIFIED requires evidence_ids")
            if status == "NOT_APPLICABLE" and not str(entry.get("note", "")).strip():
                errors.append(f"{label} {eid} NOT_APPLICABLE requires a note")
            runtime_ids = []
            for evidence_id in evidence:
                if not isinstance(evidence_id, str) or not evidence_id.strip():
                    errors.append(f"{label} {eid} has invalid evidence id")
                    continue
                if evidence_id in known_test_ids:
                    runtime_ids.append(evidence_id)
                    if status == "VERIFIED" and evidence_id not in usable_test_ids:
                        errors.append(f"{label} {eid} cites runtime evidence {evidence_id} that is not BOUND_PASS")
                    if eid not in support_map.get(evidence_id, set()):
                        errors.append(f"{label} {eid} cites {evidence_id}, but that test does not declare support for {eid}")
                elif evidence_id.startswith("T"):
                    errors.append(f"{label} {eid} cites unknown runtime evidence {evidence_id}")
                elif not evidence_id.startswith(("STATIC:", "SOURCE:", "REQUIREMENT:", "HISTORICAL:", "FINDING:")):
                    errors.append(f"{label} {eid} evidence id {evidence_id!r} has no recognized evidence class")
            if label == "acceptance" and status == "VERIFIED" and risk.get("behavioral_changed") and not any(x in usable_test_ids for x in runtime_ids):
                errors.append(f"acceptance {eid} VERIFIED for a behavioral change requires bound passing runtime evidence")

    required_lenses = set(risk.get("required_lenses", []))
    for lens in required_lenses:
        entry = lmap.get(lens)
        if not entry:
            errors.append(f"missing required review lens {lens}")
            continue
        if entry.get("status") not in LENS_STATUSES:
            errors.append(f"lens {lens} has invalid status")
        if entry.get("status") == "NOT_APPLICABLE" and not str(entry.get("note", "")).strip():
            errors.append(f"lens {lens} NOT_APPLICABLE requires a note")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate requirement/invariant/lens coverage for an n8n change review")
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--risk", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--bound-evidence", required=True)
    args = parser.parse_args()
    try:
        errors = validate(args.requirements, args.risk, args.coverage, args.bound_evidence)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("PASS: coverage valid")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
