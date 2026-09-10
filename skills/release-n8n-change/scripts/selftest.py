#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile
from pathlib import Path
from common import fingerprint

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def run(args, env=None, ok=True):
    p=subprocess.run([sys.executable,*args],text=True,capture_output=True,env=env)
    if ok and p.returncode!=0: raise AssertionError(p.stdout+p.stderr)
    if not ok and p.returncode==0: raise AssertionError("expected failure: "+" ".join(args))
    return p

with tempfile.TemporaryDirectory() as td:
    d=Path(td)
    candidate={"id":"w1","name":"Example","nodes":[{"id":"n1","name":"Start","type":"n8n-nodes-base.manualTrigger","typeVersion":1,"position":[0,0],"parameters":{}}],"connections":{},"settings":{"executionOrder":"v1"},"versionId":"NEW"}
    source={**candidate,"versionId":"OLD"}
    assert fingerprint(candidate)==fingerprint(source)
    fp=fingerprint(candidate)
    cfg=json.loads((ROOT/"assets/release-config.example.json").read_text()); cfg.update({"base_url":"https://prod.example.test","allowed_hosts":["prod.example.test"],"api_key_env":"SELFTEST_KEY","allow_production_mutation":True})
    plan=json.loads((ROOT/"assets/release-plan.example.json").read_text()); plan.update({"workflow_id":"w1","candidate_fingerprint":fp,"expected_source_fingerprint":fp})
    review=json.loads((ROOT/"assets/review-verdict.example.json").read_text()); review.update({"workflow_id":"w1","candidate_fingerprint":fp,"verdict":"PASS"})
    for name,obj in [("release-config.json",cfg),("release-plan.json",plan),("review-verdict.json",review),("candidate.json",candidate)]: (d/name).write_text(json.dumps(obj))
    for name in ["rollback-plan.example.json","postrelease-plan.example.json"]: (d/name.replace(".example","" )).write_text((ROOT/"assets"/name).read_text())
    env=dict(os.environ); env["SELFTEST_KEY"]="dummy"
    run([str(HERE/"release_preflight.py"),"--config",str(d/"release-config.json"),"--plan",str(d/"release-plan.json"),"--review",str(d/"review-verdict.json"),"--candidate",str(d/"candidate.json")],env=env)
    changed=dict(candidate); changed["settings"]={"executionOrder":"v1","executionTimeout":3}; (d/"changed.json").write_text(json.dumps(changed))
    run([str(HERE/"release_preflight.py"),"--config",str(d/"release-config.json"),"--plan",str(d/"release-plan.json"),"--review",str(d/"review-verdict.json"),"--candidate",str(d/"changed.json")],env=env,ok=False)
    review2=dict(review); review2["verdict"]="PASS_WITH_CONDITIONS"; review2["conditions"]=[{"id":"C1","release_blocking":True,"status":"OPEN"}]; (d/"review2.json").write_text(json.dumps(review2))
    run([str(HERE/"release_preflight.py"),"--config",str(d/"release-config.json"),"--plan",str(d/"release-plan.json"),"--review",str(d/"review2.json"),"--candidate",str(d/"candidate.json")],env=env,ok=False)
    run([str(HERE/"validate_release_artifacts.py"),str(d)])
print("SELFTEST PASS")
