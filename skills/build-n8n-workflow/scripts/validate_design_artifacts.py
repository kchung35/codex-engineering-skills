#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from pathlib import Path
from common import load_json, dump_json

CARDINALITY={"ZERO_OR_ONE_ITEM","EXACTLY_ONE_ITEM","ZERO_TO_MANY_ITEMS","ONE_TO_MANY_ITEMS","MANY_ITEMS","ONE_AGGREGATE_ITEM","ONE_ITEM"}
SIDE_CLASSES={"READ","CREATE","UPDATE","DELETE","SEND","SEND/PUBLISH","PUBLISH","EXECUTE","UNKNOWN"}

def validate_contracts(d):
    e=[]; w=[]
    if d.get("schema_version")!=1: e.append("contracts.schema_version must be 1")
    b=d.get("boundaries")
    if not isinstance(b,list) or not b: e.append("contracts.boundaries must be a non-empty list"); return e,w
    names=[]
    for i,x in enumerate(b):
        if not isinstance(x,dict): e.append(f"contracts.boundaries[{i}] must be object"); continue
        name=x.get("name"); names.append(name)
        if not isinstance(name,str) or not name.strip(): e.append(f"contracts.boundaries[{i}] missing name")
        c=x.get("cardinality")
        if c not in CARDINALITY: w.append(f"boundary {name or i}: cardinality {c!r} is not a standard seed value; verify semantics")
        fields=x.get("fields",[])
        if not isinstance(fields,list): e.append(f"boundary {name or i}: fields must be list"); continue
        f_names=[]
        for j,f in enumerate(fields):
            if not isinstance(f,dict): e.append(f"boundary {name or i} field[{j}] must be object"); continue
            fn=f.get("name"); f_names.append(fn)
            if not isinstance(fn,str) or not fn.strip(): e.append(f"boundary {name or i} field[{j}] missing name")
            if not f.get("type"): e.append(f"boundary {name or i} field {fn}: type required")
            if "required" not in f: w.append(f"boundary {name or i} field {fn}: required semantics not explicit")
            if "nullable" not in f: w.append(f"boundary {name or i} field {fn}: nullable semantics not explicit")
        if len([x for x in f_names if x]) != len(set(x for x in f_names if x)):
            e.append(f"boundary {name or i}: duplicate field names")
    if len([x for x in names if x]) != len(set(x for x in names if x)):
        e.append("duplicate boundary names")
    return e,w

def validate_side_effects(d):
    e=[]; w=[]
    if d.get("schema_version")!=1: e.append("side-effects.schema_version must be 1")
    nodes=d.get("nodes")
    if not isinstance(nodes,list): e.append("side-effects.nodes must be a list"); return e,w
    seen=set()
    for i,n in enumerate(nodes):
        if not isinstance(n,dict): e.append(f"side-effects.nodes[{i}] must be object"); continue
        name=n.get("node")
        if not name: e.append(f"side-effects.nodes[{i}] missing node")
        if name in seen: e.append(f"duplicate side-effect manifest entry: {name}")
        seen.add(name)
        c=n.get("classification")
        if c not in SIDE_CLASSES: e.append(f"side-effect {name}: invalid classification {c!r}")
        if c=="UNKNOWN": e.append(f"side-effect {name}: UNKNOWN must be resolved")
        if c not in (None,"READ","UNKNOWN"):
            if not n.get("idempotency"): e.append(f"side-effect {name}: idempotency decision required for {c}")
            if not n.get("retry_owner"): w.append(f"side-effect {name}: retry_owner should be explicit")
        if not n.get("system"): w.append(f"side-effect {name}: system not identified")
        if not n.get("operation"): w.append(f"side-effect {name}: operation not identified")
    return e,w

def validate_failure_policy(d):
    e=[]; w=[]
    if d.get("schema_version")!=1: e.append("failure-policy.schema_version must be 1")
    fs=d.get("failures")
    if not isinstance(fs,list): e.append("failure-policy.failures must be a list")
    else:
        for i,f in enumerate(fs):
            if not isinstance(f,dict): e.append(f"failure[{i}] must be object"); continue
            if not f.get("class"): e.append(f"failure[{i}] missing class")
            if "retry" not in f: e.append(f"failure[{i}] missing retry decision")
            if not f.get("final_action"): e.append(f"failure[{i}] missing final_action")
            if f.get("retry") is True and not f.get("max_attempts"):
                w.append(f"failure {f.get('class',i)}: retry enabled without explicit max_attempts")
    state=d.get("state")
    if not isinstance(state,dict): e.append("failure-policy.state must be object")
    else:
        for k in ["idempotency_key","concurrency","reprocessing"]:
            if not state.get(k): w.append(f"failure-policy.state.{k} is not explicit")
    return e,w

def validate_plan(d):
    e=[]; w=[]
    if d.get("schema_version")!=1: e.append("implementation-plan.schema_version must be 1")
    ops=d.get("operations")
    if not isinstance(ops,list) or not ops: e.append("implementation-plan.operations must be a non-empty list"); return e,w
    ids=[]
    allowed={"ADD","UPDATE","REMOVE","REWIRE","EXTRACT_SUBWORKFLOW","MOVE","RENAME"}
    for i,o in enumerate(ops):
        if not isinstance(o,dict): e.append(f"operation[{i}] must be object"); continue
        ids.append(o.get("id"))
        if not o.get("id"): e.append(f"operation[{i}] missing id")
        if str(o.get("action","")).upper() not in allowed: w.append(f"operation {o.get('id',i)}: uncommon action {o.get('action')!r}")
        for k in ["target","reason","test_obligation"]:
            if not o.get(k): e.append(f"operation {o.get('id',i)} missing {k}")
        for k in ["contract_change","side_effect_change"]:
            if k not in o: w.append(f"operation {o.get('id',i)} missing {k}")
    if len([x for x in ids if x])!=len(set(x for x in ids if x)): e.append("duplicate implementation operation ids")
    return e,w

VALIDATORS={
    "contracts.json":validate_contracts,
    "side-effects.json":validate_side_effects,
    "failure-policy.json":validate_failure_policy,
    "implementation-plan.json":validate_plan,
}

def validate_dir(path: Path):
    report={"errors":[],"warnings":[],"files":{}}
    for name,fn in VALIDATORS.items():
        p=path/name
        if not p.exists(): continue
        try: data=load_json(p)
        except Exception as ex:
            e=[f"{name}: invalid JSON: {ex}"]; w=[]
        else: e,w=fn(data)
        report["files"][name]={"errors":e,"warnings":w}
        report["errors"] += [f"{name}: {x}" for x in e]
        report["warnings"] += [f"{name}: {x}" for x in w]
    return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("build_dir"); ap.add_argument("--report")
    a=ap.parse_args(); r=validate_dir(Path(a.build_dir))
    if a.report: dump_json(r,a.report)
    else:
        import json; print(json.dumps(r,indent=2))
    sys.exit(1 if r["errors"] else 0)
if __name__=="__main__": main()
