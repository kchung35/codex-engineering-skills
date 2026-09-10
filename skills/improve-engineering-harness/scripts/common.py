from __future__ import annotations
import json
from pathlib import Path

STAGES = ["INTAKE","EVIDENCE","CLASSIFY","CAUSAL_MODEL","REMEDIATION","PLAN","IMPLEMENT","REGRESSION","EVALUATE","ROLLOUT","CLOSE"]

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def nonempty(v):
    return v is not None and v != "" and v != [] and v != {}

def die(messages, code=1):
    if isinstance(messages, str): messages=[messages]
    for m in messages: print(m)
    raise SystemExit(code)
