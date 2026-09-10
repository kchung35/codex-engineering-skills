#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

STAGES = [
    "BASELINE", "MODEL", "HYPOTHESES", "EXPERIMENTS", "CAUSAL_CLOSURE",
    "FIX_DESIGN", "IMPLEMENT", "VERIFY", "CLOSE"
]


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Cannot read {path}: {e}")


def nonempty(value):
    return value not in (None, "", [], {})


def jsonl_records(path):
    records = []
    p = Path(path)
    if not p.exists():
        return records
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception as e:
            raise ValueError(f"Invalid JSONL {p}:{i}: {e}")
    return records


def validate(case_dir: Path, target: str):
    errors = []
    case = load_json(case_dir / "case.json")
    model = load_json(case_dir / "system_model.json")
    hyp = load_json(case_dir / "hypotheses.json")
    causal = load_json(case_dir / "causal_set.json")
    fix = load_json(case_dir / "fix.json")
    ver = load_json(case_dir / "verification.json")
    obs = jsonl_records(case_dir / "observations.jsonl")
    exps = jsonl_records(case_dir / "experiments.jsonl")

    target_index = STAGES.index(target)

    if target_index >= STAGES.index("MODEL"):
        fs = case.get("failure_signature", {})
        if not nonempty(fs.get("observed")): errors.append("failure_signature.observed is empty")
        if not nonempty(fs.get("expected")): errors.append("failure_signature.expected is empty")
        if not obs: errors.append("no observations recorded")

    if target_index >= STAGES.index("HYPOTHESES"):
        scope = model.get("scope", {})
        if not nonempty(scope.get("relevant_nodes")) and not nonempty(model.get("external_dependencies")):
            errors.append("system model has no relevant nodes or external dependencies")

    if target_index >= STAGES.index("EXPERIMENTS"):
        hypotheses = hyp.get("hypotheses", [])
        if not hypotheses: errors.append("no hypotheses recorded")
        for h in hypotheses:
            for key in ("id", "class", "mechanism", "status"):
                if not nonempty(h.get(key)): errors.append(f"hypothesis missing {key}: {h}")

    if target_index >= STAGES.index("CAUSAL_CLOSURE"):
        # Experiments are strongly expected for ambiguous cases, but a mechanically proven case may have none.
        if not exps:
            direct_proof = any(o.get("epistemic") in ("OBSERVED", "TESTED") for o in obs)
            if not direct_proof:
                errors.append("no experiments and no direct observed/tested evidence")

    if target_index >= STAGES.index("FIX_DESIGN"):
        if causal.get("closure_status") != "SUFFICIENT_FOR_FIX":
            errors.append("causal_set.closure_status must be SUFFICIENT_FOR_FIX")
        if not causal.get("causes"):
            errors.append("causal_set has no confirmed/contributing causes")
        material_unresolved = causal.get("material_unresolved", [])
        if material_unresolved:
            errors.append(f"material unresolved causes remain: {material_unresolved}")

    if target_index >= STAGES.index("IMPLEMENT"):
        if not nonempty(fix.get("selected_option")):
            errors.append("no selected fix option")
        if not fix.get("acceptance_tests"):
            errors.append("no acceptance tests defined")

    if target_index >= STAGES.index("VERIFY"):
        impl = fix.get("implementation", {})
        if impl.get("status") not in ("DONE", "READY_FOR_VERIFY"):
            errors.append("implementation.status must be DONE or READY_FOR_VERIFY")
        if not impl.get("changes"):
            errors.append("implementation changes are empty")

    if target_index >= STAGES.index("CLOSE"):
        if ver.get("overall") != "PASS":
            errors.append("verification.overall must be PASS")
        tests = ver.get("tests", [])
        if not tests:
            errors.append("verification has no tests")
        if any(t.get("result") == "FAIL" for t in tests):
            errors.append("at least one verification test failed")
        closeout = (case_dir / "closeout.md").read_text(encoding="utf-8").strip()
        if len(closeout) < 80:
            errors.append("closeout.md is not meaningfully populated")

    return errors, case


def main():
    p = argparse.ArgumentParser(description="Validate and optionally advance a debugging case stage.")
    p.add_argument("case_dir")
    p.add_argument("--to", required=True, choices=STAGES)
    p.add_argument("--advance", action="store_true", help="Set case.json stage after gates pass")
    args = p.parse_args()

    case_dir = Path(args.case_dir)
    try:
        errors, case = validate(case_dir, args.to)
    except Exception as e:
        print(f"GATE ERROR: {e}", file=sys.stderr)
        return 2

    if errors:
        print(f"BLOCKED -> {args.to}")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"READY -> {args.to}")
    if args.advance:
        case["stage"] = args.to
        (case_dir / "case.json").write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
        print("stage advanced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
