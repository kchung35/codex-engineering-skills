from __future__ import annotations
import argparse
from common import load_json, nonempty, die, STAGES

def main():
    p=argparse.ArgumentParser(); p.add_argument('case'); a=p.parse_args(); x=load_json(a.case)
    errs=[]
    for k in ['case_id','title','status','stage','severity','failure_statement']:
        if not nonempty(x.get(k)): errs.append(f"missing {k}")
    if x.get('stage') not in STAGES: errs.append('invalid stage')
    if x.get('severity') not in ['LOW','MEDIUM','HIGH','CRITICAL']: errs.append('invalid severity')
    if errs: die([f"BLOCKED: {e}" for e in errs])
    print('PASS case schema')
if __name__=='__main__': main()
