#!/usr/bin/env python3
from __future__ import annotations
import argparse
from common import load_json,dump_json,direct_edges,node_map

def build(wf):
    nodes=node_map(wf)
    edges=direct_edges(wf)
    outgoing={n:[] for n in nodes}; incoming={n:[] for n in nodes}
    for s,t,typ,oi,ii in edges:
        outgoing.setdefault(s,[]).append({"node":t,"type":typ,"output_index":oi,"input_index":ii})
        incoming.setdefault(t,[]).append({"node":s,"type":typ,"output_index":oi,"input_index":ii})
    roots=[n for n in nodes if not incoming.get(n)]
    leaves=[n for n in nodes if not outgoing.get(n)]
    return {
      "nodes":[{"name":n,"id":v.get("id"),"type":v.get("type"),"typeVersion":v.get("typeVersion")} for n,v in nodes.items()],
      "edges":[{"source":s,"target":t,"type":typ,"output_index":oi,"input_index":ii} for s,t,typ,oi,ii in edges],
      "roots":roots,"leaves":leaves,"incoming":incoming,"outgoing":outgoing
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workflow"); ap.add_argument("--out")
    a=ap.parse_args(); result=build(load_json(a.workflow))
    if a.out: dump_json(result,a.out)
    else:
        import json; print(json.dumps(result,indent=2))
if __name__=="__main__": main()
