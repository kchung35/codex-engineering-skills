#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, secrets
from pathlib import Path
from common import dump_json, VALID_CLASSES

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--class", dest="change_class", choices=VALID_CLASSES, required=True)
    p.add_argument("--mode", choices=["NEW","MODIFY"], default="MODIFY")
    p.add_argument("--root", default=".agent-builds")
    p.add_argument("--id")
    a=p.parse_args()
    build_id=a.id or f"BUILD-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"
    d=Path(a.root)/build_id
    d.mkdir(parents=True, exist_ok=False)
    (d/"artifacts").mkdir()
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    dump_json({
        "schema_version":1,
        "id":build_id,
        "title":a.title,
        "mode":a.mode,
        "change_class":a.change_class,
        "stage":"SCOPE",
        "source_workflow": None,
        "candidate_workflow": None,
        "created_at":now,
        "updated_at":now
    }, d/"build.json")
    print(d)

if __name__=="__main__":
    main()
