#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import load_json, workflow_fingerprints, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute stable review fingerprints for an n8n workflow JSON")
    parser.add_argument("workflow")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        workflow = load_json(args.workflow)
        if not isinstance(workflow, dict) or not isinstance(workflow.get("nodes", []), list):
            raise ValueError("workflow must be a JSON object with a nodes array")
        result = {
            "schema_version": 1,
            "workflow": str(Path(args.workflow).resolve()),
            **workflow_fingerprints(workflow),
        }
        if args.out:
            write_json(result, args.out)
        else:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
