from __future__ import annotations
import argparse
from pathlib import Path
from common import load_json, nonempty, die, STAGES, save_json

def count_jsonl(path):
    if not path.exists(): return 0
    return sum(1 for l in path.read_text(encoding='utf-8').splitlines() if l.strip())

def checks(d,to):
    c=load_json(d/'case.json'); cl=load_json(d/'classification.json'); cm=load_json(d/'causal-model.json'); pr=load_json(d/'proposal.json'); evp=load_json(d/'evaluation-plan.json'); ev=load_json(d/'evaluation.json'); ro=load_json(d/'rollout.json'); e=[]
    idx=STAGES.index(to)
    if idx>=STAGES.index('EVIDENCE'):
        if not nonempty(c.get('failure_statement')): e.append('failure_statement empty')
        if count_jsonl(d/'signals.jsonl')<1: e.append('no signals recorded')
    if idx>=STAGES.index('CLASSIFY') and cl.get('primary') in [None,'','UNCLASSIFIED']: e.append('classification unresolved')
    if idx>=STAGES.index('REMEDIATION'):
        n=count_jsonl(d/'signals.jsonl')
        severe=c.get('severity') in ['HIGH','CRITICAL'] and nonempty(c.get('single_case_exception'))
        reproducible=c.get('deterministic_reproducer') is True
        if n < 2 and not reproducible and not severe:
            e.append('ordinary harness change needs >=2 signals, deterministic reproducer, or documented HIGH/CRITICAL exception')
    if idx>=STAGES.index('CAUSAL_MODEL'):
        if not nonempty(cm.get('primary_mechanism')): e.append('causal primary_mechanism empty')
        if idx>=STAGES.index('REMEDIATION') and cm.get('status')!='SUFFICIENT_FOR_REMEDIATION': e.append('causal-model.status must be SUFFICIENT_FOR_REMEDIATION')
    if idx>=STAGES.index('REMEDIATION'):
        if pr.get('classification') != cl.get('primary'): e.append('proposal classification does not match classified primary mechanism')
        for k in ['classification','mechanism','selected_remediation','change_summary','why_this_layer','regression_obligation']:
            if not nonempty(pr.get(k)): e.append(f'proposal.{k} empty')
        if pr.get('selected_remediation')=='NEW_SKILL' and not pr.get('new_skill_boundary'): e.append('new Skill boundary evidence missing')
    if idx>=STAGES.index('PLAN'):
        if not evp.get('failing_cases'): e.append('evaluation plan has no failing cases')
        if not evp.get('metrics'): e.append('evaluation plan has no metrics')
        if pr.get('blast_radius') in ['BROAD','ORGANIZATION'] and not evp.get('control_cases'): e.append('broad change has no control cases')
    if idx>=STAGES.index('REGRESSION') and not ev.get('required_case_results'): e.append('no regression case results')
    if idx>=STAGES.index('EVALUATE') and ev.get('overall') not in ['PASS','FAIL']: e.append('evaluation.overall must be PASS or FAIL')
    if pr.get('blast_radius') in ['BROAD','ORGANIZATION'] and ro.get('required') is not True: e.append('broad/organization harness change must require rollout')
    if idx>=STAGES.index('ROLLOUT') and ro.get('required') and ro.get('status') not in ['PLANNED','IN_PROGRESS','COMPLETE','ROLLED_BACK']: e.append('rollout status invalid')
    if to=='CLOSE':
        if ev.get('overall')!='PASS': e.append('evaluation is not PASS')
        if ro.get('required') and ro.get('status')!='COMPLETE': e.append('required rollout not COMPLETE')
        if len((d/'closeout.md').read_text(encoding='utf-8').strip())<80: e.append('closeout too short')
    return e

def main():
    p=argparse.ArgumentParser(); p.add_argument('case_dir'); p.add_argument('--to',required=True,choices=STAGES); p.add_argument('--advance',action='store_true'); a=p.parse_args(); d=Path(a.case_dir)
    errs=checks(d,a.to)
    if errs: die([f'BLOCKED -> {a.to}']+['- '+x for x in errs])
    if a.advance:
        c=load_json(d/'case.json'); c['stage']=a.to; save_json(d/'case.json',c)
    print(f'PASS -> {a.to}')
if __name__=='__main__': main()
