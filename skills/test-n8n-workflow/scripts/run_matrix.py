#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from n8n_api import load_lab_config


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve(base, value):
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def run_cmd(args):
    proc = subprocess.run(args, text=True, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def main():
    p = argparse.ArgumentParser(description="Run a serial fixture/assertion matrix against one deployed lab workflow")
    p.add_argument("--config", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--matrix", required=True)
    p.add_argument("--artifacts-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--continue-on-failure", action="store_true")
    args = p.parse_args()
    try:
        cfg = load_lab_config(args.config)
        matrix_path = Path(args.matrix).resolve()
        matrix = load_json(matrix_path)
        if matrix.get("schema_version") != 1 or not isinstance(matrix.get("cases"), list):
            raise ValueError("matrix must have schema_version=1 and a cases array")
        cases = matrix["cases"]
        max_cases = int(cfg.get("max_cases_per_matrix", 25))
        if len(cases) > max_cases:
            raise ValueError(f"matrix has {len(cases)} cases; configured max is {max_cases}")
        ids = [c.get("id") for c in cases if isinstance(c, dict)]
        if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x.strip() for x in ids):
            raise ValueError("matrix case ids must be unique non-empty strings")

        root = Path(args.artifacts_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        here = Path(__file__).resolve().parent
        results, overall = [], True
        for case in cases:
            cid = case["id"]
            fixture = resolve(matrix_path.parent, case.get("fixture", ""))
            assertions = resolve(matrix_path.parent, case.get("assertions", ""))
            if not fixture.is_file() or not assertions.is_file():
                raise ValueError(f"case {cid!r} fixture/assertions file not found")
            case_dir = root / cid
            case_dir.mkdir(parents=True, exist_ok=True)
            invocation, execution, assertion_result = case_dir / "invocation.json", case_dir / "execution.json", case_dir / "assertions.json"
            stages = []
            commands = [
                ("trigger", [sys.executable, str(here / "trigger_webhook.py"), "--config", args.config, "--deployment", args.deployment, "--fixture", str(fixture), "--out", str(invocation)]),
                ("capture", [sys.executable, str(here / "wait_execution.py"), "--config", args.config, "--deployment", args.deployment, "--invocation", str(invocation), "--out", str(execution)]),
                ("assert", [sys.executable, str(here / "assert_execution.py"), "--execution", str(execution), "--assertions", str(assertions), "--out", str(assertion_result)]),
            ]
            case_pass = True
            for stage, command in commands:
                rc, stdout, stderr = run_cmd(command)
                stages.append({"stage": stage, "returncode": rc, "stdout": stdout[-4000:], "stderr": stderr[-4000:]})
                if rc != 0:
                    case_pass = False
                    break
            results.append({"id": cid, "passed": case_pass, "fixture": str(fixture), "assertions": str(assertions), "artifacts_dir": str(case_dir), "stages": stages})
            overall = overall and case_pass
            print(f"{'PASS' if case_pass else 'FAIL'}: {cid}")
            if not case_pass and not args.continue_on_failure:
                break

        summary = {
            "schema_version": 1,
            "passed": overall and len(results) == len(cases),
            "counts": {"planned": len(cases), "executed": len(results), "passed": sum(1 for r in results if r["passed"]), "failed": sum(1 for r in results if not r["passed"])},
            "results": results,
        }
        write_json(summary, args.out)
        return 0 if summary["passed"] else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
