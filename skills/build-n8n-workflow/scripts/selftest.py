#!/usr/bin/env python3
from __future__ import annotations
import tempfile,json,subprocess,sys
from pathlib import Path
from common import dump_json
from validate_workflow import validate
from audit_expressions import audit
from sanitize_candidate import sanitize

BASE={
 "name":"Example",
 "nodes":[
   {"id":"1","name":"Manual Trigger","type":"n8n-nodes-base.manualTrigger","typeVersion":1,"position":[0,0],"parameters":{}},
   {"id":"2","name":"Normalize","type":"n8n-nodes-base.code","typeVersion":2,"position":[240,0],"parameters":{"jsCode":"return $input.all();"}},
   {"id":"3","name":"Output","type":"n8n-nodes-base.set","typeVersion":3.4,"position":[480,0],"parameters":{"assignments":{"assignments":[{"name":"source","value":"={{ $('Normalize').item.json.source }}","type":"string"}]}}}
 ],
 "connections":{
   "Manual Trigger":{"main":[[{"node":"Normalize","type":"main","index":0}]]},
   "Normalize":{"main":[[{"node":"Output","type":"main","index":0}]]}
 },
 "settings":{"executionOrder":"v1"}
}
def run(cmd,cwd):
    r=subprocess.run([sys.executable,*cmd],cwd=cwd,text=True,capture_output=True)
    if r.returncode!=0:
        raise AssertionError(f"command failed {cmd}\nSTDOUT:{r.stdout}\nSTDERR:{r.stderr}")
    return r
def main():
    here=Path(__file__).resolve().parent
    r=validate(BASE); assert not r["errors"],r
    ar=audit(BASE); assert not ar["errors"],ar
    broken=json.loads(json.dumps(BASE)); broken["nodes"][2]["parameters"]["assignments"]["assignments"][0]["value"]="={{ $('Missing').item.json.x }}"
    assert audit(broken)["errors"]
    dirty=json.loads(json.dumps(BASE)); dirty.update({"id":"x","active":True,"versionId":"v","createdAt":"x"}); dirty["nodes"][0]["createdAt"]="x"
    clean,stripped=sanitize(dirty,"update")
    assert "id" not in clean and "active" not in clean and "createdAt" not in clean
    assert "createdAt" not in clean["nodes"][0]
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/"BUILD-test"; d.mkdir(); (d/"artifacts").mkdir()
        dump_json({"schema_version":1,"id":"BUILD-test","title":"t","mode":"MODIFY","change_class":"FLOW","stage":"SCOPE"},d/"build.json")
        dump_json(BASE,d/"source-workflow.json")
        dump_json({"schema_version":1,"title":"t","must_do":["x"],"must_not_do":[],"invariants":[],"acceptance":[{"id":"A1","statement":"x","testable":True}],"out_of_scope":[],"unknowns":[]},d/"requirements.json")
        dump_json({"schema_version":1,"boundaries":[{"name":"x","cardinality":"ONE_ITEM","fields":[],"invariants":[],"retry_safe":True}]},d/"contracts.json")
        dump_json({"schema_version":1,"operations":[{"id":"P1","action":"UPDATE","target":"Normalize","reason":"x","contract_change":"none","side_effect_change":"none","dependencies":[],"test_obligation":"x"}]},d/"implementation-plan.json")
        dump_json({"schema_version":1,"correlation_fields":["entity_id"],"stages":["normalize"],"evidence_after_side_effect":[],"sensitive_fields_never_log":["credential"]},d/"observability.json")
        dump_json(BASE,d/"candidate-workflow.json")
        dump_json(r,d/"validation.json")
        dump_json(ar,d/"expression-audit.json")
        dump_json({"summary":{},"risk_flags":[]},d/"impact.json")
        dump_json({"test_obligations":["A1"]},d/"handoff.json")
        run(["validate_design_artifacts.py",str(d),"--report",str(d/"design-validation.json")],here)
        run(["build_gate.py",str(d),"--to","HANDOFF"],here)
        run(["analyze_workflow.py",str(d/"candidate-workflow.json"),"--out",str(d/"analysis.json")],here)
        run(["workflow_graph.py",str(d/"candidate-workflow.json"),"--out",str(d/"graph.json")],here)
        run(["sanitize_candidate.py",str(d/"candidate-workflow.json"),"--mode","update","--out",str(d/"payload.json")],here)
    print("build-n8n-workflow selftest: PASS")
if __name__=="__main__": main()
