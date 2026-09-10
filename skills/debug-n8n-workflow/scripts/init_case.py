#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:48] or "incident"


def dump(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Initialize a durable n8n debugging case ledger.")
    p.add_argument("--root", default=".agent-cases")
    p.add_argument("--title", required=True)
    p.add_argument("--case-id")
    args = p.parse_args()

    now = datetime.now(timezone.utc)
    case_id = args.case_id or f"CASE-{now.strftime('%Y%m%d-%H%M%S')}-{slugify(args.title)[:20]}"
    root = Path(args.root)
    case_dir = root / case_id
    case_dir.mkdir(parents=True, exist_ok=False)
    (case_dir / "artifacts").mkdir()

    dump(case_dir / "case.json", {
        "case_id": case_id,
        "title": args.title,
        "status": "OPEN",
        "stage": "BASELINE",
        "created_at": now.isoformat(),
        "environment": {
            "target": "unknown",
            "n8n_instance": None,
            "workflow_id": None,
            "workflow_name": None,
            "execution_ids": []
        },
        "failure_signature": {
            "observed": "",
            "expected": "",
            "impact": "",
            "reproduction": "unknown"
        },
        "constraints": [],
        "assumptions": [],
        "containment": []
    })
    (case_dir / "observations.jsonl").write_text("", encoding="utf-8")
    dump(case_dir / "system_model.json", {
        "scope": {"entry_boundary": [], "impact_boundary": [], "relevant_nodes": []},
        "edges": [], "data_contracts": [], "cross_node_references": [], "subworkflows": [],
        "state_stores": [], "external_dependencies": [], "credential_references": [],
        "side_effects": [], "retry_idempotency": [], "timing_concurrency": [],
        "versions_settings": [], "first_divergence_candidate": None, "unknowns": []
    })
    dump(case_dir / "hypotheses.json", {"hypotheses": []})
    (case_dir / "experiments.jsonl").write_text("", encoding="utf-8")
    dump(case_dir / "causal_set.json", {
        "closure_status": "OPEN", "causes": [], "relationships": [],
        "material_unresolved": [], "residual_unknowns": []
    })
    dump(case_dir / "fix.json", {
        "options": [], "selected_option": None, "selection_rationale": "",
        "invariants_preserved": [], "acceptance_tests": [],
        "implementation": {"status": "NOT_STARTED", "changes": [], "pre_change_snapshot": None}
    })
    dump(case_dir / "verification.json", {
        "environment": {}, "tests": [], "overall": "NOT_RUN", "unverified_risks": []
    })
    (case_dir / "closeout.md").write_text("# Incident Closeout\n\n", encoding="utf-8")

    print(case_dir)


if __name__ == "__main__":
    main()
