#!/usr/bin/env python3
from __future__ import annotations
import argparse,sys
from pathlib import Path
from common import load_json,class_at_least,VALID_CLASSES,VALID_MODES,is_nonempty
from validate_requirements import validate as validate_req
from validate_design_artifacts import validate_dir as validate_design_dir

STAGES=["SCOPE","CONTEXT","REQUIREMENTS","BOUNDARIES","DECISION","CONTRACTS","PLAN","BUILD","STATIC_VALIDATE","HANDOFF"]

def j(path):
    try: return load_json(path)
    except Exception: return None

def gate(d:Path,target:str):
    errs=[]; warns=[]
    build=j(d/"build.json")
    if not build: return ["missing/invalid build.json"],[]
    cls=build.get("change_class"); mode=build.get("mode")
    if cls not in VALID_CLASSES: errs.append("invalid change_class")
    if mode not in VALID_MODES: errs.append("mode must be NEW or MODIFY")
    if target not in STAGES: errs.append("invalid target stage"); return errs,warns
    t=STAGES.index(target)

    if mode=="MODIFY" and t>=STAGES.index("CONTEXT") and not (d/"source-workflow.json").exists():
        errs.append("MODIFY build requires source-workflow.json")

    need_req=class_at_least(cls or "", "FLOW")
    if need_req and t>=STAGES.index("REQUIREMENTS"):
        req=j(d/"requirements.json")
        if not req: errs.append("missing/invalid requirements.json")
        else:
            re, rw=validate_req(req); errs += [f"requirements: {x}" for x in re]; warns += [f"requirements: {x}" for x in rw]

    if class_at_least(cls or "","ARCHITECTURAL") and t>=STAGES.index("DECISION"):
        dec=j(d/"decision.json")
        if not dec: errs.append("ARCHITECTURAL build requires decision.json")
        elif not is_nonempty(dec.get("selected")) or not is_nonempty(dec.get("rationale")):
            errs.append("decision.json needs selected and rationale")

    if class_at_least(cls or "","FLOW") and t>=STAGES.index("CONTRACTS") and not (d/"contracts.json").exists():
        errs.append("FLOW+ build requires contracts.json")

    if class_at_least(cls or "","INTEGRATION") and t>=STAGES.index("PLAN"):
        side=j(d/"side-effects.json")
        if not side: errs.append("INTEGRATION+ build requires side-effects.json")
        else:
            for n in side.get("nodes",[]):
                if n.get("classification")=="UNKNOWN": errs.append(f"unresolved side effect: {n.get('node')}")
        if not (d/"failure-policy.json").exists(): errs.append("INTEGRATION+ build requires failure-policy.json")

    if class_at_least(cls or "","FLOW") and t>=STAGES.index("PLAN") and not (d/"implementation-plan.json").exists():
        errs.append("FLOW+ build requires implementation-plan.json")
    if class_at_least(cls or "","FLOW") and t>=STAGES.index("PLAN") and not (d/"observability.json").exists():
        errs.append("FLOW+ build requires observability.json")

    if t>=STAGES.index("PLAN"):
        dr=validate_design_dir(d)
        errs += [f"design artifacts: {x}" for x in dr.get("errors",[])]
        warns += [f"design artifacts: {x}" for x in dr.get("warnings",[])]

    if t>=STAGES.index("STATIC_VALIDATE") and not (d/"candidate-workflow.json").exists():
        errs.append("candidate-workflow.json is required")

    if t>=STAGES.index("STATIC_VALIDATE"):
        val=j(d/"validation.json")
        aud=j(d/"expression-audit.json")
        if not val: errs.append("missing validation.json")
        elif val.get("errors"): errs.append(f"static validation has {len(val['errors'])} blocking error(s)")
        if not aud: errs.append("missing expression-audit.json")
        elif aud.get("errors"): errs.append(f"expression audit has {len(aud['errors'])} blocking error(s)")
        if mode=="MODIFY" and not (d/"impact.json").exists(): errs.append("MODIFY build requires impact.json")

    if t>=STAGES.index("HANDOFF") and need_req:
        hp=j(d/"handoff.json")
        if not hp: errs.append("FLOW+ build requires handoff.json")
        elif not hp.get("test_obligations"): errs.append("handoff.json requires test_obligations")

    return errs,warns

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("build_dir"); ap.add_argument("--to",required=True,choices=STAGES)
    a=ap.parse_args(); e,w=gate(Path(a.build_dir),a.to)
    for x in e: print("BLOCK:",x)
    for x in w: print("WARN:",x)
    if e: print(f"BLOCKED -> {a.to}"); sys.exit(1)
    print(f"PASS -> {a.to}")
if __name__=="__main__": main()
