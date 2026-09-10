#!/usr/bin/env python3
import argparse, datetime as dt
from common import dump_json, fingerprint, load_json, sanitized_update_payload
from n8n_api import N8NClient

p=argparse.ArgumentParser()
for x in ["config","plan","baseline","candidate","out"]: p.add_argument("--"+x,required=True)
p.add_argument("--confirm-production-mutation",action="store_true")
a=p.parse_args()
if not a.confirm_production_mutation: raise SystemExit("BLOCKED: --confirm-production-mutation required")
cfg,plan,base,cand=map(load_json,[a.config,a.plan,a.baseline,a.candidate]); client=N8NClient(cfg["base_url"],cfg["api_key_env"],cfg.get("request_timeout_seconds",20)); cur=client.get_workflow(plan["workflow_id"])
if fingerprint(cur)!=base["workflow_fingerprint"] or cur.get("activeVersionId")!=base.get("active_version_id"): raise SystemExit("PRODUCTION_DRIFT: workflow changed since baseline capture")
resp=client.update_workflow_draft(plan["workflow_id"],sanitized_update_payload(cand)); after=client.get_workflow(plan["workflow_id"]); approved=plan["candidate_fingerprint"]
if fingerprint(after)!=approved: raise SystemExit("STAGE_MISMATCH: staged draft does not equal approved candidate")
if after.get("activeVersionId")!=base.get("active_version_id"): raise SystemExit("UNEXPECTED_PUBLICATION: active version changed during draft staging")
version=after.get("versionId") or resp.get("versionId")
if not version: raise SystemExit("STAGE_MISMATCH: no staged versionId observed")
out={"staged_at":dt.datetime.now(dt.timezone.utc).isoformat(),"workflow_id":plan["workflow_id"],"candidate_fingerprint":approved,"staged_version_id":version,"active_version_id_after_stage":after.get("activeVersionId")}
dump_json(a.out,out); print("OK: staged version",version)
