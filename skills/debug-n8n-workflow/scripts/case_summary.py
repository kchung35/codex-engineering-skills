#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def count_jsonl(path):
    p = Path(path)
    return sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip()) if p.exists() else 0


def main():
    p = argparse.ArgumentParser(description="Print a compact debugging-case status summary.")
    p.add_argument("case_dir")
    args = p.parse_args()
    d = Path(args.case_dir)

    case = load(d / "case.json")
    h = load(d / "hypotheses.json").get("hypotheses", [])
    causal = load(d / "causal_set.json")
    fix = load(d / "fix.json")
    ver = load(d / "verification.json")

    states = {}
    for x in h:
        states[x.get("status", "UNKNOWN")] = states.get(x.get("status", "UNKNOWN"), 0) + 1

    print(f"Case: {case.get('case_id')} — {case.get('title')}")
    print(f"Stage: {case.get('stage')} | Status: {case.get('status')}")
    print(f"Observations: {count_jsonl(d / 'observations.jsonl')} | Experiments: {count_jsonl(d / 'experiments.jsonl')}")
    print(f"Hypotheses: {len(h)} {states}")
    print(f"Causal closure: {causal.get('closure_status')} | Causes: {len(causal.get('causes', []))} | Material unresolved: {len(causal.get('material_unresolved', []))}")
    print(f"Selected fix: {fix.get('selected_option') or 'none'} | Implementation: {fix.get('implementation', {}).get('status')}")
    print(f"Verification: {ver.get('overall')} | Tests: {len(ver.get('tests', []))}")


if __name__ == "__main__":
    main()
