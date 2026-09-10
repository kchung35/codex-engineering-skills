#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run(*args: str, expect: int | None = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(HERE / args[0]), *args[1:]], text=True, capture_output=True)
    if expect is not None and proc.returncode != expect:
        raise AssertionError(f"{args[0]} returned {proc.returncode}, expected {expect}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def base_workflow() -> dict:
    return {
        "id": "wf1",
        "name": "Example",
        "nodes": [
            {"id": "n1", "name": "Start", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "parameters": {}},
            {"id": "n2", "name": "Normalize", "type": "n8n-nodes-base.set", "typeVersion": 3, "position": [200, 0], "parameters": {"assignments": {"assignments": []}}},
        ],
        "connections": {"Start": {"main": [[{"node": "Normalize", "type": "main", "index": 0}]]}},
        "settings": {"executionOrder": "v1"},
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = base_workflow()
        candidate = base_workflow()
        candidate["nodes"].append({
            "id": "n3", "name": "Send", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
            "position": [400, 0], "parameters": {"method": "POST", "url": "https://lab.example.test/items"},
            "credentials": {"httpHeaderAuth": {"id": "cred-lab", "name": "Lab"}},
        })
        candidate["connections"]["Normalize"] = {"main": [[{"node": "Send", "type": "main", "index": 0}]]}
        requirements = {
            "schema_version": 1,
            "title": "Send normalized record",
            "acceptance": [{"id": "A1", "statement": "One normalized record is sent", "testable": True}],
            "invariants": ["Existing normalized output remains valid"],
        }
        write(root / "source.json", source)
        write(root / "candidate.json", candidate)
        write(root / "requirements.json", requirements)

        review_dir = root / "review"
        run("init_review.py", "--title", "Selftest", "--mode", "MODIFY", "--change-class", "INTEGRATION",
            "--source", str(root / "source.json"), "--candidate", str(root / "candidate.json"),
            "--requirements", str(root / "requirements.json"), "--out-dir", str(review_dir))
        run("validate_review_packet.py", str(review_dir / "review.json"))
        run("workflow_diff.py", "--source", str(review_dir / "artifacts/source-workflow.json"),
            "--candidate", str(review_dir / "artifacts/candidate-workflow.json"), "--out", str(review_dir / "workflow-diff.json"))
        run("risk_scan.py", "--candidate", str(review_dir / "artifacts/candidate-workflow.json"),
            "--diff", str(review_dir / "workflow-diff.json"), "--out", str(review_dir / "risk-scan.json"))
        diff = json.loads((review_dir / "workflow-diff.json").read_text())
        risk = json.loads((review_dir / "risk-scan.json").read_text())
        assert diff["behavioral_changed"] is True
        assert "integration" in risk["required_lenses"]
        assert "state-idempotency" in risk["required_lenses"]
        assert "security" in risk["required_lenses"]

        # Create a bound passing runtime test against the exact candidate snapshot.
        test_dir = root / "test-artifacts"
        test_dir.mkdir()
        plan = {
            "schema_version": 1,
            "test_id": "T1",
            "question": "Does the candidate send the normalized record?",
            "strategy": "BOUNDARY_REPLAY",
            "source": {"workflow_snapshot": "candidate-under-test.json"},
            "cases": [{"id": "case1"}],
        }
        write(test_dir / "candidate-under-test.json", candidate)
        write(test_dir / "test-plan.json", plan)
        write(test_dir / "summary.json", {"schema_version": 1, "passed": True, "counts": {"planned": 1, "executed": 1, "passed": 1, "failed": 0}})
        manifest = {"schema_version": 1, "tests": [{"id": "T1", "test_plan": str(test_dir / "test-plan.json"), "summary": str(test_dir / "summary.json"), "supports": ["A1", "I1"]}]}
        write(review_dir / "test-evidence.json", manifest)
        run("bind_test_evidence.py", "--candidate", str(review_dir / "artifacts/candidate-workflow.json"),
            "--manifest", str(review_dir / "test-evidence.json"), "--out", str(review_dir / "bound-test-evidence.json"))
        bound = json.loads((review_dir / "bound-test-evidence.json").read_text())
        assert bound["tests"][0]["state"] == "BOUND_PASS"

        fp = bound["candidate_behavior_sha256"]
        findings = {"schema_version": 1, "candidate_behavior_sha256": fp, "findings": []}
        write(review_dir / "findings.json", findings)
        coverage = {
            "schema_version": 1,
            "candidate_behavior_sha256": fp,
            "acceptance": [{"id": "A1", "status": "VERIFIED", "evidence_ids": ["T1"], "note": "runtime"}],
            "invariants": [{"id": "I1", "statement": requirements["invariants"][0], "status": "VERIFIED", "evidence_ids": ["T1"], "note": "runtime"}],
            "lenses": [{"id": lens, "status": "REVIEWED", "evidence_ids": ["T1"], "finding_ids": []} for lens in risk["required_lenses"]],
        }
        write(review_dir / "coverage.json", coverage)
        run("validate_findings.py", str(review_dir / "findings.json"))
        run("validate_coverage.py", "--requirements", str(review_dir / "artifacts/requirements.json"),
            "--risk", str(review_dir / "risk-scan.json"), "--coverage", str(review_dir / "coverage.json"),
            "--bound-evidence", str(review_dir / "bound-test-evidence.json"))
        pass_proc = run("review_gate.py", "--packet", str(review_dir / "review.json"), "--diff", str(review_dir / "workflow-diff.json"),
            "--risk", str(review_dir / "risk-scan.json"), "--findings", str(review_dir / "findings.json"),
            "--coverage", str(review_dir / "coverage.json"), "--bound-evidence", str(review_dir / "bound-test-evidence.json"),
            "--out", str(review_dir / "verdict.json"))
        assert pass_proc.stdout.strip() == "PASS"

        # A confirmed HIGH defect must reject.
        finding = {
            "id": "R-001", "severity": "HIGH", "category": "state-idempotency", "status": "OPEN",
            "claim": "POST can duplicate on retry", "evidence": ["STATIC:HTTP_WRITE_CHANGED"],
            "failure_scenario": "Remote write succeeds and retry repeats it", "impact": "Duplicate record",
            "affected_requirements": ["A1"], "affected_invariants": [],
            "required_action": "Provide idempotency", "verification_needed": "Replay twice", "confidence": "HIGH"
        }
        write(review_dir / "findings.json", {"schema_version": 1, "candidate_behavior_sha256": fp, "findings": [finding]})
        reject_proc = run("review_gate.py", "--packet", str(review_dir / "review.json"), "--diff", str(review_dir / "workflow-diff.json"),
            "--risk", str(review_dir / "risk-scan.json"), "--findings", str(review_dir / "findings.json"),
            "--coverage", str(review_dir / "coverage.json"), "--bound-evidence", str(review_dir / "bound-test-evidence.json"),
            "--out", str(review_dir / "verdict-reject.json"), expect=1)
        assert reject_proc.stdout.strip() == "REJECT"

        # Test evidence from a stale candidate must not satisfy the gate.
        stale = base_workflow()
        write(test_dir / "candidate-under-test.json", stale)
        run("bind_test_evidence.py", "--candidate", str(review_dir / "artifacts/candidate-workflow.json"),
            "--manifest", str(review_dir / "test-evidence.json"), "--out", str(review_dir / "bound-stale.json"))
        stale_bound = json.loads((review_dir / "bound-stale.json").read_text())
        assert stale_bound["tests"][0]["state"] == "STALE"

        # Visual/editor-only changes must not create a fake runtime-test obligation.
        layout_a = base_workflow()
        layout_b = base_workflow()
        layout_b["nodes"][1]["position"] = [999, 999]
        write(root / "layout-a.json", layout_a)
        write(root / "layout-b.json", layout_b)
        run("workflow_diff.py", "--source", str(root / "layout-a.json"), "--candidate", str(root / "layout-b.json"), "--out", str(root / "layout-diff.json"))
        run("risk_scan.py", "--candidate", str(root / "layout-b.json"), "--diff", str(root / "layout-diff.json"), "--out", str(root / "layout-risk.json"))
        layout_diff = json.loads((root / "layout-diff.json").read_text())
        layout_risk = json.loads((root / "layout-risk.json").read_text())
        assert layout_diff["behavioral_changed"] is False
        assert set(layout_risk["required_lenses"]) == {"requirements", "scope-diff"}

    print("PASS: review harness self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
