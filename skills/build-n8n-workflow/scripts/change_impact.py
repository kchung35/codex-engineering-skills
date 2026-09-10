#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from common import load_json,dump_json,direct_edges

VOLATILE_NODE={"createdAt","updatedAt"}
def norm_node(n):
    return {k:v for k,v in n.items() if k not in VOLATILE_NODE}
def by_identity(wf):
    out={}
    for n in wf.get("nodes",[]):
        key=("id",n.get("id")) if n.get("id") else ("name",n.get("name"))
        out[key]=n
    return out
def change_fields(a,b):
    keys=set(a)|set(b); return sorted(k for k in keys if a.get(k)!=b.get(k))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--before",required=True); ap.add_argument("--after",required=True); ap.add_argument("--out")
    x=load_json(a.before); y=load_json(a.after)
    xb=by_identity(x); ya=by_identity(y)
    added=[]; removed=[]; modified=[]
    for k,n in ya.items():
        if k not in xb: added.append({"identity":k,"name":n.get("name"),"type":n.get("type")})
        else:
            fields=change_fields(norm_node(xb[k]),norm_node(n))
            if fields: modified.append({"identity":k,"name_before":xb[k].get("name"),"name_after":n.get("name"),"fields":fields,
                                        "credentials_changed":"credentials" in fields,"parameters_changed":"parameters" in fields})
    for k,n in xb.items():
        if k not in ya: removed.append({"identity":k,"name":n.get("name"),"type":n.get("type")})
    before_edges={(s,t,typ,oi,ii) for s,t,typ,oi,ii in direct_edges(x)}
    after_edges={(s,t,typ,oi,ii) for s,t,typ,oi,ii in direct_edges(y)}
    settings_changed=change_fields(x.get("settings") or {},y.get("settings") or {})
    risk=[]
    if removed: risk.append("nodes_removed")
    if settings_changed: risk.append("workflow_settings_changed")
    if any(m["credentials_changed"] for m in modified): risk.append("credential_references_changed")
    if before_edges != after_edges: risk.append("control_flow_changed")
    result={
      "added_nodes":added,"removed_nodes":removed,"modified_nodes":modified,
      "added_edges":[list(e) for e in sorted(after_edges-before_edges)],
      "removed_edges":[list(e) for e in sorted(before_edges-after_edges)],
      "settings_changed":settings_changed,
      "risk_flags":risk,
      "summary":{"added":len(added),"removed":len(removed),"modified":len(modified),
                 "edge_additions":len(after_edges-before_edges),"edge_removals":len(before_edges-after_edges)}
    }
    if a.out: dump_json(result,a.out)
    else: print(json.dumps(result,indent=2))
if __name__=="__main__": main()
