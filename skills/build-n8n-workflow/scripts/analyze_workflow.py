#!/usr/bin/env python3
from __future__ import annotations
import argparse
from collections import Counter
from common import load_json,dump_json,direct_edges,walk_strings
from audit_expressions import refs

def is_trigger(n):
    t=str(n.get("type","")).lower()
    return "trigger" in t or t.endswith(".webhook")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workflow"); ap.add_argument("--out")
    a=ap.parse_args(); wf=load_json(a.workflow)
    nodes=wf.get("nodes",[]); edges=direct_edges(wf)
    cred=[]; code=[]; refs_out=[]; webhooks=[]; subs=[]; retry=[]; error_modes=[]
    for n in nodes:
        if n.get("credentials"):
            cred.append({"node":n.get("name"),"credential_types":sorted((n.get("credentials") or {}).keys())})
        if str(n.get("type","")).lower().endswith(".code"):
            code.append({"node":n.get("name"),"typeVersion":n.get("typeVersion")})
        if n.get("webhookId") or str(n.get("type","")).lower().endswith(".webhook"):
            webhooks.append({"node":n.get("name"),"webhookId":n.get("webhookId")})
        if "executeworkflow" in str(n.get("type","")).lower() or "subworkflow" in str(n.get("type","")).lower():
            subs.append({"node":n.get("name"),"type":n.get("type")})
        if n.get("retryOnFail"):
            retry.append({"node":n.get("name"),"maxTries":n.get("maxTries"),"waitBetweenTries":n.get("waitBetweenTries")})
        if n.get("onError") or n.get("continueOnFail"):
            error_modes.append({"node":n.get("name"),"onError":n.get("onError"),"continueOnFail":n.get("continueOnFail")})
        for path,text in walk_strings(n.get("parameters",{})):
            for r in refs(text): refs_out.append({"node":n.get("name"),"reference":r,"parameter":".".join(path)})
    out={
      "name":wf.get("name"),
      "node_count":len(nodes),
      "edge_count":len(edges),
      "node_types":dict(Counter(str(n.get("type")) for n in nodes)),
      "triggers":[n.get("name") for n in nodes if is_trigger(n)],
      "credential_references":cred,
      "code_nodes":code,
      "cross_node_references":refs_out,
      "webhooks":webhooks,
      "subworkflow_nodes":subs,
      "retry_nodes":retry,
      "error_modes":error_modes,
      "has_static_data":bool(wf.get("staticData")),
      "has_pin_data":bool(wf.get("pinData")),
      "settings":wf.get("settings") or {},
    }
    if a.out: dump_json(out,a.out)
    else:
        import json; print(json.dumps(out,indent=2))
if __name__=="__main__": main()
