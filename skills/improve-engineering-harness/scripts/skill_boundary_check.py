from __future__ import annotations
import argparse
from common import load_json, die

def main():
    p=argparse.ArgumentParser(); p.add_argument('proposal'); a=p.parse_args(); x=load_json(a.proposal)
    if x.get('selected_remediation')!='NEW_SKILL':
        print('PASS new-skill boundary not applicable'); return
    b=x.get('new_skill_boundary') or {}
    req=['distinct_user_intent','different_procedure','different_tools_or_safety','independently_useful','not_stage_of_existing','not_deterministic_only','not_reference_only','routing_nonoverlap']
    bad=[k for k in req if b.get(k) is not True]
    if bad: die(['BLOCKED NEW_SKILL: '+', '.join(bad)])
    print('PASS new-skill boundary')
if __name__=='__main__': main()
