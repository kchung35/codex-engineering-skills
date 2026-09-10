#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import load_json
p=argparse.ArgumentParser(); p.add_argument("release_dir"); a=p.parse_args(); r=Path(a.release_dir)

def get(name):
    p=r/name
    return load_json(p) if p.exists() else {}
plan=get("release-plan.json"); base=get("production-baseline.json"); staged=get("staged-release.json"); pub=get("publication.json"); control=get("control-plane-verification.json"); runtime=get("runtime-verification.json"); rb=get("rollback-result.json"); post=get("postrelease-plan.json")
print("release_id:",plan.get("release_id")); print("workflow_id:",plan.get("workflow_id")); print("candidate:",plan.get("candidate_fingerprint")); print("baseline_active:",base.get("active_version_id")); print("staged_version:",staged.get("staged_version_id")); print("published_version:",pub.get("published_version_id")); print("control_plane:",control.get("status")); print("runtime:",runtime.get("status") if runtime else ("LIMITED" if post.get("strategy")=="CONTROL_PLANE_ONLY" else "MISSING")); print("rollback:",rb.get("status","NOT_USED"))
