from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
from common import save_json

def slug(s):
    s=re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
    return s[:40] or "case"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--root", default=".agent-harness")
    p.add_argument("--case-id")
    a=p.parse_args()
    now=datetime.now(timezone.utc)
    cid=a.case_id or f"HARNESS-{now.strftime('%Y%m%d-%H%M%S')}-{slug(a.title)}"
    d=Path(a.root)/cid; (d/'artifacts').mkdir(parents=True, exist_ok=False)
    save_json(d/'case.json', {"case_id":cid,"title":a.title,"status":"OPEN","stage":"INTAKE","severity":"MEDIUM","scope":"REPOSITORY","failure_statement":"","impact":"","signal_ids":[],"affected_capabilities":[],"epistemic_notes":[],"constraints":[],"out_of_scope":[],"deterministic_reproducer":False,"single_case_exception":"","created_at":now.isoformat()})
    (d/'signals.jsonl').write_text('',encoding='utf-8')
    for name,obj in {
      'classification.json':{"primary":"UNCLASSIFIED","contributing":[],"rationale":"","confidence":"LOW"},
      'causal-model.json':{"status":"OPEN","primary_mechanism":"","chain":[],"alternatives":[],"evidence":[]},
      'proposal.json':{"proposal_id":"P001","classification":"","mechanism":"","selected_remediation":"","target_components":[],"change_summary":"","why_this_layer":"","alternatives_rejected":[],"blast_radius":"LOCAL","reversibility":"HIGH","new_skill_boundary":None,"regression_obligation":"","security_impact":"NONE"},
      'evaluation-plan.json':{"plan_id":"EV001","failure_mechanism":"","before_artifact":"","after_artifact":"","failing_cases":[],"control_cases":[],"metrics":[],"protected_metrics":[],"stochastic_trials":1,"acceptance_rules":[],"rollback_triggers":[]},
      'evaluation.json':{"plan_id":"EV001","artifact":"AFTER","runs":[],"metrics":{},"required_case_results":[],"overall":"UNKNOWN","notes":[]},
      'rollout.json':{"required":False,"status":"NOT_REQUIRED","scope":"LOCAL","previous_version":"","new_version":"","rollback_trigger":"","rollback_procedure":"","notes":[]}
    }.items(): save_json(d/name,obj)
    (d/'closeout.md').write_text('# Harness improvement closeout\n\n',encoding='utf-8')
    print(d)
if __name__=='__main__': main()
