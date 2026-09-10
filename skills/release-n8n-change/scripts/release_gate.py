#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import load_json
p=argparse.ArgumentParser(); p.add_argument("release_dir"); p.add_argument("--to",required=True,choices=["STAGE","PUBLISH","CLOSE"]); a=p.parse_args(); root=Path(a.release_dir); errors=[]

def need(name):
    path=root/name
    if not path.exists(): errors.append(f"missing {name}"); return None
    return load_json(path)
plan=need("release-plan.json"); review=need("review-verdict.json"); cfg=need("release-config.json")
if review and review.get("verdict") not in {"PASS","PASS_WITH_CONDITIONS"}: errors.append("review verdict not releasable")
if a.to in {"STAGE","PUBLISH","CLOSE"}:
    base=need("production-baseline.json"); rb=need("rollback-plan.json")
    if base and not base.get("workflow_fingerprint"): errors.append("baseline fingerprint missing")
    if base and base.get("was_published") and not base.get("rollback_version_id"): errors.append("published baseline lacks rollback version")
if a.to in {"PUBLISH","CLOSE"}:
    staged=need("staged-release.json")
    if staged and not staged.get("staged_version_id"): errors.append("staged version ID missing")
if a.to=="CLOSE":
    pub=need("publication.json"); control=need("control-plane-verification.json")
    if pub and pub.get("status")!="CONFIRMED": errors.append("publication not confirmed")
    if control and control.get("status")!="PASS": errors.append("control-plane verification did not pass")
    post=need("postrelease-plan.json")
    if post and post.get("strategy")!="CONTROL_PLANE_ONLY":
        runtime=need("runtime-verification.json")
        if runtime and runtime.get("status")!="PASS": errors.append("runtime verification did not pass")
if errors:
    print("BLOCKED ->",a.to); [print("-",e) for e in errors]; raise SystemExit(2)
print("OK ->",a.to)
