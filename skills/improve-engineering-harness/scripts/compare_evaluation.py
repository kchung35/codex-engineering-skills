from __future__ import annotations
import argparse, json
from common import load_json, save_json

def main():
    p=argparse.ArgumentParser(); p.add_argument('--plan',required=True); p.add_argument('--before',required=True); p.add_argument('--after',required=True); p.add_argument('--out'); a=p.parse_args()
    plan,bef,aft=load_json(a.plan),load_json(a.before),load_json(a.after)
    rows=[]; overall='PASS'
    for m in list(plan.get('metrics',[])) + list(plan.get('protected_metrics',[])):
        name=m['name']; b=bef.get('metrics',{}).get(name); x=aft.get('metrics',{}).get(name); status='PASS'
        if b is None or x is None: status='UNKNOWN'
        else:
            d=m.get('direction','MAXIMIZE')
            if 'minimum_after' in m and x < m['minimum_after']: status='FAIL'
            if 'maximum_after' in m and x > m['maximum_after']: status='FAIL'
            maxreg=m.get('maximum_regression')
            if maxreg is not None:
                if d=='MAXIMIZE' and b-x>maxreg: status='FAIL'
                if d=='MINIMIZE' and x-b>maxreg: status='FAIL'
        if status=='FAIL': overall='FAIL'
        elif status=='UNKNOWN' and overall=='PASS': overall='UNKNOWN'
        rows.append({'name':name,'before':b,'after':x,'status':status})
    out={'overall':overall,'metrics':rows}
    if a.out: save_json(a.out,out)
    else: print(json.dumps(out,indent=2))
    raise SystemExit(0 if overall=='PASS' else 1)
if __name__=='__main__': main()
