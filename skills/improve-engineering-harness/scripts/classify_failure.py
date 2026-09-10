from __future__ import annotations
import argparse, json
from common import load_json, save_json

CATS={
'ROUTING_AMBIGUITY':['wrong skill','route','routing','overlap','ambiguous skill'],
'CONTEXT_DISCOVERY':['could not find','not discover','hidden doc','context','source of truth'],
'KNOWLEDGE_STALENESS':['stale','outdated','obsolete','changed api','docs disagree'],
'MISSING_INVARIANT':['invariant','always','must never','rule missing'],
'DETERMINISTIC_REASONING_GAP':['manual diff','manual parse','manually inspect','calculation','deterministic'],
'TOOL_CAPABILITY_GAP':['no tool','cannot access','missing api','missing connector'],
'ENVIRONMENT_LEGIBILITY':['logs','trace','version unknown','opaque','cannot inspect'],
'FEEDBACK_LOOP_GAP':['too late','ci','feedback','not caught'],
'TEST_COVERAGE_GAP':['missing test','no fixture','regression escaped','not tested'],
'EVIDENCE_BINDING_GAP':['stale evidence','wrong version','fingerprint','unbound'],
'SAFETY_ENFORCEMENT_GAP':['unsafe','production mutation','permission','authorization','safety gate'],
'SKILL_SCOPE_GAP':['existing skill missing','skill lacks'],
'SKILL_OVERLAP':['skills overlap','duplicate skill','same intent'],
'MODEL_INTERFACE_GAP':['unstructured','schema','ambiguous output','free form'],
'PROCESS_GAP':['handoff','ordering','process','lifecycle']}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--text'); p.add_argument('--case'); p.add_argument('--out'); a=p.parse_args()
    text=a.text or ''
    if a.case:
        c=load_json(a.case); text+=' '+c.get('failure_statement','')+' '+c.get('impact','')
    low=text.lower(); scores={k:sum(low.count(w) for w in ws) for k,ws in CATS.items()}
    primary=max(scores,key=scores.get) if max(scores.values(), default=0)>0 else 'UNCLASSIFIED'
    ranked=[{"category":k,"score":v} for k,v in sorted(scores.items(),key=lambda z:(-z[1],z[0])) if v>0]
    out={"primary":primary,"scores":ranked,"method":"keyword-routing-signal","note":"Heuristic signal only; confirm mechanism from evidence."}
    if a.out: save_json(a.out,out)
    else: print(json.dumps(out,indent=2))
if __name__=='__main__': main()
