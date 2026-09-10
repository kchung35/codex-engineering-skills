#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys
from common import load_json

def validate(d):
    errors=[]; warnings=[]
    if d.get("schema_version") != 1: errors.append("schema_version must be 1")
    for k in ["must_do","must_not_do","invariants","acceptance","out_of_scope","unknowns"]:
        if k not in d: errors.append(f"missing key: {k}")
        elif not isinstance(d[k], list): errors.append(f"{k} must be a list")
    if not d.get("must_do"): errors.append("must_do must contain at least one required behavior")
    if not d.get("acceptance"): errors.append("acceptance must contain at least one criterion")
    ids=set()
    for i,item in enumerate(d.get("acceptance",[])):
        if isinstance(item,str):
            warnings.append(f"acceptance[{i}] is unstructured; prefer id/statement/testable")
            continue
        if not isinstance(item,dict):
            errors.append(f"acceptance[{i}] must be object or string"); continue
        for k in ["id","statement","testable"]:
            if k not in item: errors.append(f"acceptance[{i}] missing {k}")
        if item.get("id") in ids: errors.append(f"duplicate acceptance id: {item.get('id')}")
        ids.add(item.get("id"))
        if item.get("testable") is not True:
            warnings.append(f"acceptance {item.get('id',i)} is not explicitly testable")
    return errors,warnings

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("requirements")
    ap.add_argument("--json", action="store_true")
    a=ap.parse_args()
    e,w=validate(load_json(a.requirements))
    if a.json:
        import json; print(json.dumps({"errors":e,"warnings":w},indent=2))
    else:
        for x in e: print("ERROR:",x)
        for x in w: print("WARN:",x)
        print(f"{len(e)} error(s), {len(w)} warning(s)")
    sys.exit(1 if e else 0)
if __name__=="__main__": main()
