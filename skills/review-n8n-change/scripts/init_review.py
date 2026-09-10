#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import workflow_fingerprints, load_json, write_json

VALID_MODES = {"NEW", "MODIFY", "REFACTOR", "MIGRATION", "BUG_FIX"}
VALID_CLASSES = {"LOCAL", "FLOW", "INTEGRATION", "STATEFUL", "ARCHITECTURAL"}


def copy_if(src: str | None, dest_dir: Path, name: str) -> str | None:
    if not src:
        return None
    source = Path(src).resolve()
    if not source.is_file():
        raise ValueError(f"file not found: {source}")
    dest = dest_dir / "artifacts" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return str(dest.relative_to(dest_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize an independent n8n change review directory")
    parser.add_argument("--title", required=True)
    parser.add_argument("--mode", required=True, choices=sorted(VALID_MODES))
    parser.add_argument("--change-class", required=True, choices=sorted(VALID_CLASSES))
    parser.add_argument("--source")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    try:
        if args.mode != "NEW" and not args.source:
            raise ValueError(f"mode {args.mode} requires --source")
        root = Path(args.out_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        source_rel = copy_if(args.source, root, "source-workflow.json")
        candidate_rel = copy_if(args.candidate, root, "candidate-workflow.json")
        requirements_rel = copy_if(args.requirements, root, "requirements.json")
        candidate = load_json(root / candidate_rel)
        fingerprint = workflow_fingerprints(candidate)
        review = {
            "schema_version": 1,
            "review_id": f"REVIEW-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "title": args.title,
            "mode": args.mode,
            "change_class": args.change_class,
            "source_workflow": source_rel,
            "candidate_workflow": candidate_rel,
            "requirements": requirements_rel,
            "build_artifacts": {},
            "debug_artifacts": {},
            "test_evidence_manifest": "test-evidence.json",
            "author_rationale": None,
            "candidate_behavior_sha256": fingerprint["behavior_sha256"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": "INTAKE",
        }
        write_json(review, root / "review.json")
        write_json({"schema_version": 1, "tests": []}, root / "test-evidence.json")
        write_json({"schema_version": 1, "candidate_behavior_sha256": fingerprint["behavior_sha256"], "findings": []}, root / "findings.json")
        write_json({
            "schema_version": 1,
            "candidate_behavior_sha256": fingerprint["behavior_sha256"],
            "acceptance": [], "invariants": [], "lenses": []
        }, root / "coverage.json")
        print(root)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
