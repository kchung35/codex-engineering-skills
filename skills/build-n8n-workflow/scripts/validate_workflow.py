#!/usr/bin/env python3
from __future__ import annotations
import argparse,sys
from common import load_json,dump_json,direct_edges

def validate(wf):
    errors=[]; warnings=[]
    for k in ["name","nodes","connections","settings"]:
        if k not in wf: errors.append(f"missing top-level key: {k}")
    if not isinstance(wf.get("name"),str) or not wf.get("name","").strip():
        errors.append("workflow name must be non-empty")
    nodes=wf.get("nodes",[])
    if not isinstance(nodes,list):
        errors.append("nodes must be a list"); nodes=[]
    conns=wf.get("connections",{})
    if not isinstance(conns,dict): errors.append("connections must be an object"); conns={}
    if not isinstance(wf.get("settings",{}),dict): errors.append("settings must be an object")

    names=[]; ids=[]; webhook_ids=[]
    for i,n in enumerate(nodes):
        if not isinstance(n,dict): errors.append(f"nodes[{i}] must be object"); continue
        name=n.get("name"); nid=n.get("id")
        if not isinstance(name,str) or not name.strip(): errors.append(f"nodes[{i}] has invalid name")
        else: names.append(name)
        if not isinstance(nid,str) or not nid.strip(): errors.append(f"node {name or i} has invalid/missing id")
        else: ids.append(nid)
        if not isinstance(n.get("type"),str) or not n.get("type"): errors.append(f"node {name or i} has invalid type")
        tv=n.get("typeVersion")
        if not isinstance(tv,(int,float)) or tv <= 0: errors.append(f"node {name or i} has invalid typeVersion")
        pos=n.get("position")
        if not (isinstance(pos,list) and len(pos)==2 and all(isinstance(x,(int,float)) for x in pos)):
            errors.append(f"node {name or i} has invalid position")
        if "parameters" not in n or not isinstance(n.get("parameters"),dict):
            errors.append(f"node {name or i} parameters must be object")
        if n.get("continueOnFail") not in (None,False):
            warnings.append(f"node {name}: continueOnFail is deprecated; prefer explicit onError semantics")
        if n.get("webhookId"): webhook_ids.append(str(n["webhookId"]))
        if str(n.get("type","")).lower().endswith(".code"):
            params=n.get("parameters",{})
            code=max([v for v in params.values() if isinstance(v,str)], key=len, default="")
            if len(code)>12000:
                warnings.append(f"node {name}: very large Code node ({len(code)} chars); review responsibility boundaries")
    dup_names=sorted({x for x in names if names.count(x)>1})
    dup_ids=sorted({x for x in ids if ids.count(x)>1})
    dup_wh=sorted({x for x in webhook_ids if webhook_ids.count(x)>1})
    if dup_names: errors.append(f"duplicate node names: {dup_names}")
    if dup_ids: errors.append(f"duplicate node ids: {dup_ids}")
    if dup_wh: errors.append(f"duplicate webhookId values: {dup_wh}")

    name_set=set(names)
    for src in conns:
        if src not in name_set: errors.append(f"connection source does not exist: {src}")
    for s,t,typ,oi,ii in direct_edges(wf):
        if t not in name_set: errors.append(f"connection {s} -> {t}: target does not exist")

    settings=wf.get("settings") or {}
    cp=settings.get("callerPolicy")
    ids_setting=settings.get("callerIds")
    if cp=="workflowsFromAList" and not ids_setting:
        errors.append("settings.callerPolicy=workflowsFromAList requires callerIds")
    if cp and cp!="workflowsFromAList" and ids_setting:
        warnings.append("settings.callerIds is set but callerPolicy is not workflowsFromAList")
    if wf.get("pinData"):
        warnings.append("workflow contains pinData; ensure pinned data is development-only and not mistaken for runtime evidence")
    if wf.get("staticData"):
        warnings.append("workflow contains staticData; verify persistent-state semantics are intentional")
    ng=wf.get("nodeGroups") or []
    if ng and not isinstance(ng,list): errors.append("nodeGroups must be a list")
    elif isinstance(ng,list):
        seen_group_ids=set(); id_set=set(ids)
        for g in ng:
            if not isinstance(g,dict): errors.append("nodeGroup must be object"); continue
            gid=g.get("id")
            if gid in seen_group_ids: errors.append(f"duplicate nodeGroup id: {gid}")
            seen_group_ids.add(gid)
            for nid in g.get("nodeIds",[]) if isinstance(g.get("nodeIds",[]),list) else []:
                if nid not in id_set: errors.append(f"nodeGroup {g.get('name')} references missing node id {nid}")
    return {"errors":errors,"warnings":warnings,"summary":{"nodes":len(nodes),"connections":len(direct_edges(wf))}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workflow"); ap.add_argument("--report")
    a=ap.parse_args(); r=validate(load_json(a.workflow))
    if a.report: dump_json(r,a.report)
    else:
        import json; print(json.dumps(r,indent=2))
    sys.exit(1 if r["errors"] else 0)
if __name__=="__main__": main()
