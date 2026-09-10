#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path
from typing import Any, Iterable

VALID_CLASSES = ["LOCAL", "FLOW", "INTEGRATION", "STATEFUL", "ARCHITECTURAL"]
CLASS_RANK = {v:i for i,v in enumerate(VALID_CLASSES)}
VALID_MODES = ["NEW", "MODIFY"]

def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def dump_json(obj: Any, path: str | Path) -> None:
    p=Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")

def sha256_json(obj: Any) -> str:
    b=json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()
    return hashlib.sha256(b).hexdigest()

def walk_strings(obj: Any, path: tuple=()) -> Iterable[tuple[tuple,str]]:
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield from walk_strings(v, path+(str(k),))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            yield from walk_strings(v, path+(str(i),))
    elif isinstance(obj, str):
        yield path,obj

def dotted(path: tuple) -> str:
    return ".".join(path)

def class_at_least(change_class: str, minimum: str) -> bool:
    return CLASS_RANK.get(change_class, -1) >= CLASS_RANK[minimum]

def is_nonempty(value: Any) -> bool:
    if value is None: return False
    if isinstance(value, str): return bool(value.strip())
    if isinstance(value, (list,dict,set,tuple)): return bool(value)
    return True

def node_map(workflow: dict) -> dict[str,dict]:
    return {str(n.get("name")): n for n in workflow.get("nodes",[]) if n.get("name") is not None}

def direct_edges(workflow: dict) -> list[tuple[str,str,str,int,int]]:
    out=[]
    conns=workflow.get("connections") or {}
    if not isinstance(conns, dict): return out
    for src, typed in conns.items():
        if not isinstance(typed, dict): continue
        for conn_type, output_lists in typed.items():
            if not isinstance(output_lists, list): continue
            for out_idx, targets in enumerate(output_lists):
                if not isinstance(targets, list): continue
                for tgt in targets:
                    if isinstance(tgt, dict) and tgt.get("node"):
                        out.append((str(src), str(tgt["node"]), str(conn_type), out_idx, int(tgt.get("index",0) or 0)))
    return out

def ancestors(workflow: dict) -> dict[str,set[str]]:
    names=set(node_map(workflow))
    rev={n:set() for n in names}
    for s,t,*_ in direct_edges(workflow):
        if t in rev and s in names: rev[t].add(s)
    result={n:set() for n in names}
    for n in names:
        stack=list(rev[n])
        seen=set()
        while stack:
            x=stack.pop()
            if x in seen: continue
            seen.add(x)
            stack.extend(rev.get(x,()))
        result[n]=seen
    return result
