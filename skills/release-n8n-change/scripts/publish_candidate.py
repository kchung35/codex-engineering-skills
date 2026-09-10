#!/usr/bin/env python3
import argparse, datetime as dt
from common import dump_json, load_json
from n8n_api import N8NClient
p=argparse.ArgumentParser()
for x in ["config","baseline","staged","out"]: p.add_argument("--"+x,required=True)
p.add_argument("--confirm-production-mutation",action="store_true")
a=p.parse_args()
if not a.confirm_production_mutation: raise SystemExit("BLOCKED: --confirm-production-mutation required")
cfg,base,staged=map(load_json,[a.config,a.baseline,a.staged]); client=N8NClient(cfg["base_url"],cfg["api_key_env"],cfg.get("request_timeout_seconds",20)); cur=client.get_workflow(staged["workflow_id"])
if cur.get("versionId")!=staged["staged_version_id"] or cur.get("activeVersionId")!=base.get("active_version_id"): raise SystemExit("BLOCKED: publication preconditions drifted")
client.publish_version(staged["workflow_id"],staged["staged_version_id"]); confirmed=client.wait_active_version(staged["workflow_id"],staged["staged_version_id"],cfg.get("publication_timeout_seconds",60),cfg.get("poll_interval_seconds",2))
out={"published_at":dt.datetime.now(dt.timezone.utc).isoformat(),"workflow_id":staged["workflow_id"],"published_version_id":staged["staged_version_id"],"observed_active_version_id":confirmed.get("activeVersionId"),"status":"CONFIRMED"}
dump_json(a.out,out); print("OK: exact staged version published")
