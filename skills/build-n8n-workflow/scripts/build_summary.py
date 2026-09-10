#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from common import load_json
def maybe(p):
    try:return load_json(p)
    except:return {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("build_dir"); a=ap.parse_args()
    d=Path(a.build_dir); b=maybe(d/"build.json"); v=maybe(d/"validation.json"); ia=maybe(d/"impact.json")
    print(f"{b.get('id','?')} | {b.get('mode','?')} | {b.get('change_class','?')} | {b.get('title','')}")
    print("candidate:", "yes" if (d/"candidate-workflow.json").exists() else "no")
    if v: print("validation:",len(v.get("errors",[])),"errors,",len(v.get("warnings",[])),"warnings")
    if ia: print("impact:",ia.get("summary",{}),"risk_flags=",ia.get("risk_flags",[]))
    present=[p.name for p in d.iterdir() if p.is_file()]
    print("artifacts:",", ".join(sorted(present)))
if __name__=="__main__": main()
