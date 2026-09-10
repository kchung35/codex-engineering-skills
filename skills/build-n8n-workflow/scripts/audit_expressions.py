#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,sys
from common import load_json,dump_json,walk_strings,dotted,node_map,ancestors,direct_edges

PATTERNS=[
    re.compile(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"\$node\[\s*['\"]([^'\"]+)['\"]\s*\]"),
]
def refs(text):
    out=[]
    for p in PATTERNS:
        out.extend(m.group(1) for m in p.finditer(text))
    return sorted(set(out))

def audit(wf):
    names=set(node_map(wf))
    anc=ancestors(wf)
    direct_in={n:set() for n in names}
    for s,t,*_ in direct_edges(wf):
        if t in direct_in: direct_in[t].add(s)
    errors=[]; warnings=[]; found=[]
    for node in wf.get("nodes",[]):
        nname=node.get("name")
        for path,text in walk_strings(node.get("parameters",{})):
            for ref in refs(text):
                rec={"node":nname,"parameter":dotted(path),"references":ref}
                if ref not in names:
                    rec["status"]="MISSING"
                    errors.append(f"{nname}:{dotted(path)} references missing node {ref!r}")
                elif ref == nname:
                    rec["status"]="SELF_REFERENCE"
                    warnings.append(f"{nname}:{dotted(path)} references itself")
                elif ref not in anc.get(nname,set()):
                    rec["status"]="NON_ANCESTOR"
                    warnings.append(f"{nname}:{dotted(path)} references {ref!r}, which is not upstream in the main graph")
                elif ref not in direct_in.get(nname,set()):
                    rec["status"]="LONG_RANGE"
                    warnings.append(f"{nname}:{dotted(path)} has long-range reference to {ref!r}")
                else:
                    rec["status"]="DIRECT_UPSTREAM"
                found.append(rec)
    return {"errors":errors,"warnings":warnings,"references":found}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workflow"); ap.add_argument("--report")
    a=ap.parse_args(); r=audit(load_json(a.workflow))
    if a.report: dump_json(r,a.report)
    else:
        import json; print(json.dumps(r,indent=2))
    sys.exit(1 if r["errors"] else 0)
if __name__=="__main__": main()
