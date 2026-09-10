#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

VOLATILE_KEYS = {"startTime", "executionTime", "executionIndex"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path=None):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def sanitize(value: Any):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def run_data(execution):
    return (((execution.get("data") or {}).get("resultData") or {}).get("runData") or {})


def semantic_execution(execution):
    return {"status": execution.get("status"), "mode": execution.get("mode"), "runData": sanitize(run_data(execution))}


def workflow_order(workflow, node_names):
    if not workflow:
        return sorted(node_names)
    order = [n.get("name") for n in workflow.get("nodes", []) if isinstance(n, dict) and n.get("name")]
    rank = {name: i for i, name in enumerate(order)}
    return sorted(node_names, key=lambda n: (rank.get(n, 10**9), n))


def compact_value(value, max_chars=500):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    if len(text) <= max_chars:
        return value
    return {"_truncated": True, "preview": text[:max_chars] + "…"}


def pointer_escape(token):
    return str(token).replace("~", "~0").replace("/", "~1")


def diff_values(a, b, pointer="", *, limit=200, out=None):
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if type(a) is not type(b):
        out.append({"pointer": pointer, "baseline": compact_value(a), "candidate": compact_value(b)})
        return out
    if isinstance(a, dict):
        for key in sorted(set(a) | set(b), key=str):
            if len(out) >= limit:
                break
            p = pointer + "/" + pointer_escape(key)
            if key not in a:
                out.append({"pointer": p, "baseline": {"_missing": True}, "candidate": compact_value(b[key])})
            elif key not in b:
                out.append({"pointer": p, "baseline": compact_value(a[key]), "candidate": {"_missing": True}})
            else:
                diff_values(a[key], b[key], p, limit=limit, out=out)
        return out
    if isinstance(a, list):
        for i in range(max(len(a), len(b))):
            if len(out) >= limit:
                break
            p = pointer + f"/{i}"
            if i >= len(a):
                out.append({"pointer": p, "baseline": {"_missing": True}, "candidate": compact_value(b[i])})
            elif i >= len(b):
                out.append({"pointer": p, "baseline": compact_value(a[i]), "candidate": {"_missing": True}})
            else:
                diff_values(a[i], b[i], p, limit=limit, out=out)
        return out
    if a != b:
        out.append({"pointer": pointer, "baseline": compact_value(a), "candidate": compact_value(b)})
    return out


def compare_executions(baseline, candidate, workflow=None, max_differences=200):
    b, c = semantic_execution(baseline), semantic_execution(candidate)
    bnodes, cnodes = b["runData"], c["runData"]
    all_nodes = set(bnodes) | set(cnodes)
    changed, per_node = [], {}
    for node in workflow_order(workflow, all_nodes):
        if node not in bnodes:
            state = "ADDED"
        elif node not in cnodes:
            state = "REMOVED"
        elif bnodes[node] == cnodes[node]:
            state = "UNCHANGED"
        else:
            state = "CHANGED"
        per_node[node] = state
        if state != "UNCHANGED":
            changed.append(node)
    diffs = diff_values(b, c, limit=max_differences)
    return {
        "schema_version": 1, "equivalent": b == c,
        "baseline": {"execution_id": baseline.get("id"), "status": baseline.get("status")},
        "candidate": {"execution_id": candidate.get("id"), "status": candidate.get("status")},
        "first_changed_node": changed[0] if changed else None,
        "changed_nodes": changed, "node_states": per_node, "differences": diffs,
        "difference_limit_reached": len(diffs) >= max_differences,
        "notes": [
            "Timing fields startTime, executionTime, and executionIndex are ignored.",
            "first_changed_node is workflow-order evidence, not a root-cause conclusion.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description="Compare two n8n executions using a deterministic semantic view")
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--workflow")
    p.add_argument("--max-differences", type=int, default=200)
    p.add_argument("--out")
    args = p.parse_args()
    try:
        result = compare_executions(load_json(args.baseline), load_json(args.candidate), load_json(args.workflow) if args.workflow else None, max_differences=args.max_differences)
        dump_json(result, args.out)
        print(f"{'EQUIVALENT' if result['equivalent'] else 'DIFFERENT'}: changed_nodes={len(result['changed_nodes'])} first={result['first_changed_node']!r}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
