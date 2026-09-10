#!/usr/bin/env python3
import argparse
from common import fingerprint, load_json
from n8n_api import N8NClient
p=argparse.ArgumentParser()
for x in ["config","baseline","staged","candidate"]: p.add_argument("--"+x,required=True)
a=p.parse_args(); cfg,base,staged,cand=map(load_json,[a.config,a.baseline,a.staged,a.candidate]); client=N8NClient(cfg["base_url"],cfg["api_key_env"],cfg.get("request_timeout_seconds",20)); cur=client.get_workflow(staged["workflow_id"])
if cur.get("versionId")!=staged["staged_version_id"]: raise SystemExit("STAGED_DRIFT: current draft versionId changed")
if fingerprint(cur)!=staged["candidate_fingerprint"] or fingerprint(cand)!=staged["candidate_fingerprint"]: raise SystemExit("STAGED_DRIFT: candidate fingerprint mismatch")
if cur.get("activeVersionId")!=base.get("active_version_id"): raise SystemExit("STAGED_DRIFT: activeVersionId changed before publication")
print("OK: staged candidate is still exact and unpublished")
