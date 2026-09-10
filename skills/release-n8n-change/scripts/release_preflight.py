#!/usr/bin/env python3
import argparse, os, sys
from urllib.parse import urlparse
from common import fingerprint, load_json

def fail(msg):
    print("BLOCKED:", msg, file=sys.stderr); raise SystemExit(2)

p = argparse.ArgumentParser()
p.add_argument("--config", required=True); p.add_argument("--plan", required=True); p.add_argument("--review", required=True); p.add_argument("--candidate", required=True)
a = p.parse_args(); cfg, plan, review, cand = map(load_json, [a.config, a.plan, a.review, a.candidate])
if cfg.get("environment_class") != "PRODUCTION": fail("environment_class must be PRODUCTION")
host = (urlparse(cfg.get("base_url", "")).hostname or "").lower(); allowed = [x.lower() for x in cfg.get("allowed_hosts", [])]
if not host or host not in allowed: fail(f"production host {host!r} is not explicitly allowlisted")
if not cfg.get("api_key_env"): fail("api_key_env missing")
if cfg.get("allow_production_mutation") is not True: fail("allow_production_mutation must be true for release execution")
if not os.environ.get(cfg["api_key_env"]): fail(f"API key env {cfg['api_key_env']} is not set")
wid = plan.get("workflow_id")
if not wid or review.get("workflow_id") != wid: fail("workflow_id mismatch between plan and review")
actual = fingerprint(cand)
if plan.get("candidate_fingerprint") != actual: fail("candidate fingerprint does not match release plan")
if review.get("candidate_fingerprint") != actual: fail("candidate fingerprint does not match review verdict")
if review.get("evidence_status", "CURRENT") != "CURRENT": fail("review evidence is not CURRENT")
verdict = review.get("verdict")
if verdict not in {"PASS", "PASS_WITH_CONDITIONS"}: fail(f"review verdict {verdict!r} is not releasable")
blocking = [c for c in review.get("conditions", []) if c.get("release_blocking", True) and c.get("status") not in {"RESOLVED", "SATISFIED"}]
if blocking: fail(f"{len(blocking)} release-blocking review condition(s) unresolved")
if not plan.get("expected_source_fingerprint"): fail("expected_source_fingerprint missing")
print("OK: release preflight passed"); print("candidate_fingerprint:", actual)
