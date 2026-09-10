#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Tuple

MISSING = object()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_pointer_get(document: Any, pointer: str):
    if pointer == "":
        return document
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON Pointer must be empty or start with '/'")
    current = document
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError):
                return MISSING
        elif isinstance(current, dict):
            if token not in current:
                return MISSING
            current = current[token]
        else:
            return MISSING
    return current


def run_data(execution):
    return (((execution.get("data") or {}).get("resultData") or {}).get("runData") or {})


def node_runs(execution, node):
    runs = run_data(execution).get(node, [])
    return runs if isinstance(runs, list) else []


def evaluate_one(execution, spec) -> Tuple[bool, str]:
    t = spec.get("type")
    if t == "status_equals":
        actual = execution.get("status")
        expected = spec.get("expected")
        return actual == expected, f"status actual={actual!r} expected={expected!r}"
    if t == "node_executed":
        runs = node_runs(execution, spec.get("node"))
        return bool(runs), f"node {spec.get('node')!r} runs={len(runs)}"
    if t == "node_not_executed":
        runs = node_runs(execution, spec.get("node"))
        return not runs, f"node {spec.get('node')!r} runs={len(runs)}"
    if t == "node_error_absent":
        runs = node_runs(execution, spec.get("node"))
        if not runs:
            return False, f"node {spec.get('node')!r} did not execute"
        errors = [r.get("error") for r in runs if isinstance(r, dict) and r.get("error")]
        return not errors, f"node {spec.get('node')!r} errors={len(errors)}"
    if t == "node_item_count":
        node = spec.get("node")
        ri = int(spec.get("run_index", 0))
        oi = int(spec.get("output_index", 0))
        runs = node_runs(execution, node)
        try:
            items = runs[ri]["data"]["main"][oi]
            actual = len(items)
        except (IndexError, KeyError, TypeError):
            return False, f"node {node!r} output r{ri}/o{oi} unavailable"
        expected = int(spec.get("expected"))
        return actual == expected, f"node {node!r} item_count actual={actual} expected={expected}"

    if t in {"json_pointer_exists", "json_pointer_equals", "json_pointer_not_equals",
             "json_pointer_matches_regex", "json_pointer_length"}:
        pointer = spec.get("pointer")
        try:
            value = json_pointer_get(execution, pointer)
        except Exception as exc:
            return False, f"pointer error: {exc}"
        if t == "json_pointer_exists":
            return value is not MISSING, f"pointer {pointer!r} {'exists' if value is not MISSING else 'missing'}"
        if value is MISSING:
            return False, f"pointer {pointer!r} missing"
        if t == "json_pointer_equals":
            expected = spec.get("expected")
            return value == expected, f"pointer {pointer!r} actual={value!r} expected={expected!r}"
        if t == "json_pointer_not_equals":
            expected = spec.get("expected")
            return value != expected, f"pointer {pointer!r} actual={value!r} forbidden={expected!r}"
        if t == "json_pointer_matches_regex":
            if not isinstance(value, str):
                return False, f"pointer {pointer!r} value is not a string"
            flags = re.IGNORECASE if "i" in str(spec.get("flags", "")) else 0
            ok = re.search(str(spec.get("pattern", "")), value, flags) is not None
            return ok, f"pointer {pointer!r} regex={spec.get('pattern')!r} actual={value!r}"
        if t == "json_pointer_length":
            if not isinstance(value, (list, dict, str)):
                return False, f"pointer {pointer!r} value has no supported length"
            actual = len(value)
            expected = int(spec.get("expected"))
            return actual == expected, f"pointer {pointer!r} length actual={actual} expected={expected}"
    return False, f"unsupported assertion type {t!r}"


def evaluate_assertions(execution, envelope):
    if envelope.get("schema_version") != 1 or not isinstance(envelope.get("assertions"), list):
        raise ValueError("assertions file must have schema_version=1 and an assertions array")
    if not envelope["assertions"]:
        raise ValueError("assertions array must not be empty")
    data_level = any(isinstance(a, dict) and a.get("type") != "status_equals" for a in envelope["assertions"])
    redacted = bool((((execution.get("data") or {}).get("redactionInfo") or {}).get("isRedacted")))
    oversized = bool(execution.get("dataTooLargeToDisplay"))
    if data_level and redacted:
        raise ValueError("INSUFFICIENT_EVIDENCE: execution data is redacted but assertions require node/data detail")
    if data_level and oversized:
        raise ValueError("INSUFFICIENT_EVIDENCE: execution data was omitted because it exceeded the n8n display limit")
    results = []
    for i, spec in enumerate(envelope["assertions"]):
        if not isinstance(spec, dict):
            results.append({"index": i, "passed": False, "detail": "assertion is not an object"})
            continue
        passed, detail = evaluate_one(execution, spec)
        results.append({"index": i, "type": spec.get("type"), "passed": bool(passed), "detail": detail})
    passed = sum(1 for r in results if r["passed"])
    return {
        "schema_version": 1,
        "passed": passed == len(results),
        "counts": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
        "results": results,
    }


def main():
    p = argparse.ArgumentParser(description="Apply deterministic assertions to n8n execution JSON")
    p.add_argument("--execution", required=True)
    p.add_argument("--assertions", required=True)
    p.add_argument("--out")
    args = p.parse_args()
    execution = load_json(args.execution)
    envelope = load_json(args.assertions)
    try:
        result = evaluate_assertions(execution, envelope)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    print(f"{'PASS' if result['passed'] else 'FAIL'}: {result['counts']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
