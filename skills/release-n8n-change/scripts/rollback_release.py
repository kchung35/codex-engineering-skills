#!/usr/bin/env python3
import argparse, datetime as dt
from common import dump_json, load_json
from n8n_api import N8NClient
p=argparse.ArgumentParser()
for x in ["config","baseline","publication","out"]: p.add_argument("--"+x,required=True)
p.add_argument("--confirm-production-mutation",action="store_true")
a=p.parse_args()
if not a.confirm_production_mutation: raise SystemExit("BLOCKED: --confirm-production-mutation required")
cfg,base,pub=map(load_json,[a.config,a.baseline,a.publication]); client=N8NClient(cfg["base_url"],cfg["api_key_env"],cfg.get("request_timeout_seconds",20)); wid=base["workflow_id"]; timeout=cfg.get("publication_timeout_seconds",60); poll=cfg.get("poll_interval_seconds",2)
if base.get("was_published"):
    target=base.get("rollback_version_id")
    if not target: raise SystemExit("ROLLBACK_UNCONFIRMED: baseline lacks rollback version")
    client.publish_version(wid,target); observed=client.wait_active_version(wid,target,timeout,poll); kind="PUBLISH_VERSION"
else:
    client.unpublish(wid); observed=client.wait_unpublished(wid,timeout,poll); target=None; kind="UNPUBLISH"
out={"rolled_back_at":dt.datetime.now(dt.timezone.utc).isoformat(),"workflow_id":wid,"rollback_kind":kind,"target_version_id":target,"observed_active_version_id":observed.get("activeVersionId"),"status":"VERIFIED"}; dump_json(a.out,out); print("OK: rollback verified")
