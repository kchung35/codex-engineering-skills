#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_fixture import digest_items


def extract_items(execution, node, run_index=0, output_index=0):
    try:
        run_data = execution["data"]["resultData"]["runData"]
        runs = run_data[node]
        run = runs[run_index]
        main = run["data"]["main"]
        items = main[output_index]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            f"cannot extract node={node!r} run_index={run_index} output_index={output_index}: {exc}"
        ) from exc
    if not isinstance(items, list):
        raise ValueError("selected node output is not an item array")
    return items


def main():
    p = argparse.ArgumentParser(description="Extract an n8n node output into a replay fixture")
    p.add_argument("--execution", required=True)
    p.add_argument("--node", required=True)
    p.add_argument("--run-index", type=int, default=0)
    p.add_argument("--output-index", type=int, default=0)
    p.add_argument("--fixture-id")
    p.add_argument("--provenance-kind", default="historical_execution")
    p.add_argument("--note", default="")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    execution = json.loads(Path(args.execution).read_text(encoding="utf-8"))
    redaction = (((execution.get("data") or {}).get("redactionInfo") or {}).get("isRedacted"))
    if redaction:
        print("ERROR: execution data is redacted; refusing to create a historical fixture", file=sys.stderr)
        return 2
    items = extract_items(execution, args.node, args.run_index, args.output_index)
    execution_id = str(execution.get("id", "unknown"))
    fixture_id = args.fixture_id or f"execution-{execution_id}-{args.node}-r{args.run_index}-o{args.output_index}"
    fixture = {
        "schema_version": 1,
        "metadata": {
            "fixture_id": fixture_id,
            "boundary_node": args.node,
            "output_index": args.output_index,
            "provenance": {
                "kind": args.provenance_kind,
                "source_execution_id": execution_id,
                "source_workflow_id": execution.get("workflowId"),
                "source_workflow_version_id": execution.get("workflowVersionId"),
                "note": args.note,
            },
            "sha256": digest_items(items),
        },
        "items": items,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE: {args.out} items={len(items)} sha256={fixture['metadata']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
