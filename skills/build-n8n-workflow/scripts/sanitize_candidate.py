#!/usr/bin/env python3
from __future__ import annotations
import argparse,copy
from common import load_json,dump_json

CREATE_ALLOWED={"name","description","nodes","connections","settings","nodeGroups","staticData","pinData","projectId","parentFolderId"}
UPDATE_ALLOWED={"name","description","nodes","connections","settings","nodeGroups","staticData","pinData","parentFolderId"}
NODE_ALLOWED={"id","name","webhookId","disabled","notesInFlow","notes","type","typeVersion","executeOnce","alwaysOutputData","retryOnFail","maxTries","waitBetweenTries","continueOnFail","onError","position","parameters","credentials","customTelemetryTags"}
DERIVED_SETTINGS={"binaryMode","credentialResolverId"}

def sanitize(wf,mode):
    allowed=CREATE_ALLOWED if mode=="create" else UPDATE_ALLOWED
    out={k:copy.deepcopy(v) for k,v in wf.items() if k in allowed}
    out["nodes"]=[]
    for node in wf.get("nodes",[]):
        out["nodes"].append({k:copy.deepcopy(v) for k,v in node.items() if k in NODE_ALLOWED})
    if isinstance(out.get("settings"),dict):
        for k in DERIVED_SETTINGS: out["settings"].pop(k,None)
    stripped=sorted(k for k in wf if k not in allowed)
    return out,stripped

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workflow"); ap.add_argument("--mode",choices=["create","update"],required=True); ap.add_argument("--out",required=True); ap.add_argument("--meta")
    a=ap.parse_args(); wf=load_json(a.workflow); out,stripped=sanitize(wf,a.mode); dump_json(out,a.out)
    if a.meta: dump_json({"mode":a.mode,"stripped_top_level":stripped,"publish_if_active":False if a.mode=="update" else None},a.meta)
if __name__=="__main__": main()
