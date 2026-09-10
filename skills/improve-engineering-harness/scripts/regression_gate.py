from __future__ import annotations
import argparse
from common import load_json, die

def main():
    p=argparse.ArgumentParser(); p.add_argument('--plan',required=True); p.add_argument('--results',required=True); a=p.parse_args()
    plan,res=load_json(a.plan),load_json(a.results); errs=[]
    byid={r.get('case_id'):r for r in res.get('required_case_results',[])}
    for cid in plan.get('failing_cases',[]):
        r=byid.get(cid)
        if not r: errs.append(f'missing failing case {cid}')
        elif r.get('status')!='PASS': errs.append(f'historical failure not fixed: {cid}={r.get("status")}')
    for cid in plan.get('control_cases',[]):
        r=byid.get(cid)
        if not r: errs.append(f'missing control case {cid}')
        elif r.get('status')!='PASS': errs.append(f'control regression: {cid}={r.get("status")}')
    for r in res.get('required_case_results',[]):
        if r.get('kind')=='SAFETY' and r.get('status')!='PASS': errs.append(f'safety regression: {r.get("case_id")}')
    if errs: die(['BLOCKED: '+e for e in errs])
    print('PASS regression gate')
if __name__=='__main__': main()
