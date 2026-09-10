#!/usr/bin/env python3
import argparse, datetime as dt
from urllib.parse import urlparse
from common import dump_json, fingerprint, load_json
from n8n_api import N8NClient

p = argparse.ArgumentParser(); p.add_argument("--config", required=True); p.add_argument("--plan", required=True); p.add_argument("--out", required=True)
a = p.parse_args(); cfg=load_json(a.config); plan=load_json(a.plan)
client=N8NClient(cfg["base_url"], cfg["api_key_env"], cfg.get("request_timeout_seconds",20)); w=client.get_workflow(plan["workflow_id"]); fp=fingerprint(w)
if fp != plan["expected_source_fingerprint"]: raise SystemExit(f"PRODUCTION_DRIFT: expected {plan['expected_source_fingerprint']} observed {fp}")
expected_active=plan.get("expected_active_version_id")
if expected_active is not None and w.get("activeVersionId") != expected_active: raise SystemExit(f"PRODUCTION_DRIFT: expected activeVersionId {expected_active} observed {w.get('activeVersionId')}")
out={"captured_at":dt.datetime.now(dt.timezone.utc).isoformat(),"host":urlparse(cfg["base_url"]).hostname,"workflow_id":w.get("id"),"workflow_name":w.get("name"),"draft_version_id":w.get("versionId"),"workflow_fingerprint":fp,"active_version_id":w.get("activeVersionId"),"was_published":bool(w.get("activeVersionId")),"rollback_kind":"PUBLISH_VERSION" if w.get("activeVersionId") else "UNPUBLISH","rollback_version_id":w.get("activeVersionId"),"workflow_snapshot":w}
dump_json(a.out,out); print("OK: baseline captured", a.out)
