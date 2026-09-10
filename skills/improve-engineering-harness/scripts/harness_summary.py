from __future__ import annotations
import argparse
from pathlib import Path
from common import load_json

def main():
    p=argparse.ArgumentParser(); p.add_argument('case_dir'); a=p.parse_args(); d=Path(a.case_dir)
    c=load_json(d/'case.json'); cl=load_json(d/'classification.json'); pr=load_json(d/'proposal.json'); ev=load_json(d/'evaluation.json'); ro=load_json(d/'rollout.json')
    sig=sum(1 for x in (d/'signals.jsonl').read_text(encoding='utf-8').splitlines() if x.strip())
    print(f"case: {c.get('case_id')} | stage: {c.get('stage')} | status: {c.get('status')}")
    print(f"signals: {sig} | classification: {cl.get('primary')}")
    print(f"remediation: {pr.get('selected_remediation') or '-'} | target: {', '.join(pr.get('target_components',[])) or '-'}")
    print(f"evaluation: {ev.get('overall')} | rollout: {ro.get('status')}")
if __name__=='__main__': main()
