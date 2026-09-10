#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import load_json
p=argparse.ArgumentParser(); p.add_argument("release_dir"); a=p.parse_args(); root=Path(a.release_dir); errors=[]
required=["release-config.json","release-plan.json","review-verdict.json","rollback-plan.json","postrelease-plan.json","candidate.json"]
for name in required:
    if not (root/name).exists(): errors.append(f"missing {name}")
if not errors:
    plan=load_json(root/"release-plan.json"); review=load_json(root/"review-verdict.json"); post=load_json(root/"postrelease-plan.json")
    if plan.get("workflow_id")!=review.get("workflow_id"): errors.append("workflow_id mismatch")
    if plan.get("candidate_fingerprint")!=review.get("candidate_fingerprint"): errors.append("candidate fingerprint mismatch")
    if plan.get("intent") not in {"PUBLISH_CHANGE","PUBLISH_PREVIOUSLY_UNPUBLISHED"}: errors.append("invalid release intent")
    if post.get("strategy") not in {"PASSIVE","SAFE_CANARY","BOUND_PRODUCTION_SMOKE","CONTROL_PLANE_ONLY"}: errors.append("invalid postrelease strategy")
if errors:
    print("BLOCKED"); [print("-",x) for x in errors]; raise SystemExit(2)
print("OK: release artifacts structurally valid")
