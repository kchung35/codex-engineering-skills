#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from common import load_json, resolve_path, workflow_fingerprints

VALID_MODES = {"NEW", "MODIFY", "REFACTOR", "MIGRATION", "BUG_FIX"}
VALID_CLASSES = {"LOCAL", "FLOW", "INTEGRATION", "STATEFUL", "ARCHITECTURAL"}


def validate(path: str) -> list[str]:
    errors: list[str] = []
    packet = load_json(path)
    if not isinstance(packet, dict) or packet.get("schema_version") != 1:
        return ["review packet must be an object with schema_version=1"]
    if packet.get("mode") not in VALID_MODES:
        errors.append("invalid or missing mode")
    if packet.get("change_class") not in VALID_CLASSES:
        errors.append("invalid or missing change_class")
    for key in ("review_id", "title", "candidate_workflow", "requirements"):
        if not isinstance(packet.get(key), str) or not packet[key].strip():
            errors.append(f"{key} must be a non-empty string")
    if packet.get("mode") != "NEW" and not packet.get("source_workflow"):
        errors.append(f"mode {packet.get('mode')} requires source_workflow")

    for key in ("candidate_workflow", "requirements", "source_workflow"):
        value = packet.get(key)
        if not value:
            continue
        resolved = resolve_path(path, value)
        if not resolved or not resolved.is_file():
            errors.append(f"{key} does not resolve to a file: {value}")

    candidate_path = resolve_path(path, packet.get("candidate_workflow"))
    if candidate_path and candidate_path.is_file():
        candidate = load_json(candidate_path)
        if not isinstance(candidate, dict) or not isinstance(candidate.get("nodes", []), list):
            errors.append("candidate_workflow is not a valid workflow object")
        else:
            actual = workflow_fingerprints(candidate)["behavior_sha256"]
            recorded = packet.get("candidate_behavior_sha256")
            if recorded and recorded != actual:
                errors.append("candidate_behavior_sha256 does not match candidate_workflow")

    req_path = resolve_path(path, packet.get("requirements"))
    if req_path and req_path.is_file():
        req = load_json(req_path)
        if not isinstance(req, dict) or req.get("schema_version") != 1:
            errors.append("requirements must have schema_version=1")
        if not isinstance(req.get("acceptance", []), list):
            errors.append("requirements.acceptance must be an array")

    for group_key in ("build_artifacts", "debug_artifacts"):
        group = packet.get(group_key, {})
        if group is not None and not isinstance(group, dict):
            errors.append(f"{group_key} must be an object")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate review packet structure and artifact identity")
    parser.add_argument("packet")
    args = parser.parse_args()
    try:
        errors = validate(args.packet)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print("PASS: review packet valid")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
