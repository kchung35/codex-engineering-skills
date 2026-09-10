#!/usr/bin/env python3
import argparse, datetime as dt
from common import dump_json, fingerprint, load_json
from n8n_api import N8NClient
p=argparse.ArgumentParser()
for x in ["config","staged","candidate","out"]: p.add_argument("--"+x,required=True)
a=p.parse_args(); cfg,staged,cand=map(load_json,[a.config,a.staged,a.candidate]); client=N8NClient(cfg["base_url"],cfg["api_key_env"],cfg.get("request_timeout_seconds",20)); cur=client.get_workflow(staged["workflow_id"])
checks={"active_version_matches":cur.get("activeVersionId")==staged["staged_version_id"],"draft_version_matches":cur.get("versionId")==staged["staged_version_id"],"candidate_fingerprint_matches":fingerprint(cur)==staged["candidate_fingerprint"]==fingerprint(cand)}
status="PASS" if all(checks.values()) else "FAIL"; out={"verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),"workflow_id":staged["workflow_id"],"status":status,"checks":checks,"observed_active_version_id":cur.get("activeVersionId"),"observed_draft_version_id":cur.get("versionId")}; dump_json(a.out,out)
if status!="PASS": raise SystemExit("CONTROL_PLANE_VERIFICATION_FAILED")
print("OK: control-plane verification passed")
