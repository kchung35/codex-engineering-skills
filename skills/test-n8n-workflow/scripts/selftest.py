#!/usr/bin/env python3
"""Offline self-tests for deterministic test-n8n-workflow mechanics."""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path

from assert_execution import evaluate_assertions
from execution_diff import compare_executions
from extract_fixture import extract_items
from make_replay_clone import compile_replay
from validate_fixture import digest_items, validate_fixture
from validate_lab_workflow import validate_workflow
from validate_test_plan import validate_plan


def sample_config():
    return {
        "schema_version": 1, "environment_class": "NON_PRODUCTION",
        "instance_base_url": "https://lab.example.invalid", "webhook_base_url": "https://lab.example.invalid",
        "project_id": "P-LAB", "workflow_name_prefix": "LAB__", "credential_reference_policy": "REQUIRE_MAP",
        "allow_external_writes": False, "allowed_test_targets": ["lab-postgres"],
        "external_deny_hosts": ["prod.example.invalid"], "production_deny_hosts": ["prod-n8n.example.invalid"],
        "max_fixture_bytes": 1048576, "max_cases_per_matrix": 25, "max_run_seconds": 180,
    }


def sample_workflow():
    return {
        "id": "WF-SOURCE", "versionId": "V1", "name": "Source Workflow",
        "nodes": [
            {"id": "n1", "name": "Source", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "parameters": {}},
            {"id": "n2", "name": "Parse", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [250, 0], "parameters": {}},
            {"id": "n3", "name": "Normalize", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [500, 0], "parameters": {"jsCode": "return $input.all();"}},
            {"id": "n4", "name": "HTTP Read", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [750, 0], "parameters": {"method": "GET", "url": "https://example.invalid/read"}},
        ],
        "connections": {
            "Source": {"main": [[{"node": "Parse", "type": "main", "index": 0}]]},
            "Parse": {"main": [[{"node": "Normalize", "type": "main", "index": 0}]]},
            "Normalize": {"main": [[{"node": "HTTP Read", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }


def sample_execution(value=7):
    return {
        "id": "E1", "status": "success", "mode": "webhook", "workflowId": "WF", "workflowVersionId": "V",
        "data": {"resultData": {"runData": {
            "Parse": [{"startTime": 1, "executionTime": 2, "data": {"main": [[{"json": {"x": value}}]]}}],
            "Normalize": [{"startTime": 3, "executionTime": 2, "data": {"main": [[{"json": {"x": value}}]]}}],
        }}},
    }


def main():
    cfg, source = sample_config(), sample_workflow()
    workflow, meta = compile_replay(cfg, source, "Parse", 0, "CASE-1", {}, connection_type="main")
    assert workflow["name"].startswith("LAB__")
    assert [n["name"] for n in workflow["nodes"]] == ["LAB Fixture Trigger", "Parse", "Normalize", "HTTP Read"]
    assert meta["removed_nodes"] == ["Source"]
    assert workflow["projectId"] == "P-LAB"

    manifest = {"schema_version": 1, "nodes": {"HTTP Read": {"classification": "READ_ONLY", "reason": "GET-only test dependency"}}}
    errors, _, report = validate_workflow(cfg, workflow, manifest, ack_writes=False)
    assert not errors, errors
    assert report["HTTP Read"] == "READ_ONLY"

    test_plan = {
        "schema_version": 1, "test_id": "CASE-1-E1", "question": "Does replay work?", "strategy": "BOUNDARY_REPLAY",
        "source": {"workflow_snapshot": "source.json"}, "boundary": {"node": "Parse", "connection_type": "main", "output_index": 0},
        "cases": [{"id": "c1", "fixture": "f.json", "assertions": "a.json"}], "side_effect_manifest": "s.json",
        "timeout_seconds": 60, "cleanup_policy": "DELETE",
    }
    perr, _ = validate_plan(cfg, test_plan)
    assert not perr, perr

    target_manifest = {"schema_version": 1, "nodes": {"HTTP Read": {"classification": "TEST_TARGET", "target": "not-allowlisted", "reason": "selftest"}}}
    terr, _, _ = validate_workflow(cfg, workflow, target_manifest, ack_writes=False)
    assert any("allowed_test_targets" in e for e in terr), terr

    execution = sample_execution(7)
    items = extract_items(execution, "Parse", 0, 0)
    fixture = {
        "schema_version": 1,
        "metadata": {"fixture_id": "F1", "boundary_node": "Parse", "output_index": 0, "provenance": {"kind": "selftest"}, "sha256": digest_items(items)},
        "items": items,
    }
    ferr, _ = validate_fixture(fixture, 1048576)
    assert not ferr, ferr
    assertions = {"schema_version": 1, "assertions": [
        {"type": "status_equals", "expected": "success"},
        {"type": "node_executed", "node": "Normalize"},
        {"type": "node_item_count", "node": "Normalize", "expected": 1},
        {"type": "json_pointer_equals", "pointer": "/data/resultData/runData/Normalize/0/data/main/0/0/json/x", "expected": 7},
    ]}
    result = evaluate_assertions(execution, assertions)
    assert result["passed"], result

    redacted = copy.deepcopy(execution)
    redacted["data"]["redactionInfo"] = {"isRedacted": True}
    try:
        evaluate_assertions(redacted, assertions)
    except ValueError as exc:
        assert "INSUFFICIENT_EVIDENCE" in str(exc)
    else:
        raise AssertionError("redacted execution data was not rejected as insufficient evidence")

    changed = sample_execution(8)
    changed["id"] = "E2"
    diff = compare_executions(execution, changed, source)
    assert not diff["equivalent"]
    assert diff["first_changed_node"] in {"Parse", "Normalize"}

    bad = sample_workflow()
    for node in bad["nodes"]:
        if node["name"] == "Normalize":
            node["parameters"]["jsCode"] = "return $('Source').all();"
    try:
        compile_replay(cfg, bad, "Parse", 0, "CASE-X", {}, connection_type="main")
    except ValueError:
        pass
    else:
        raise AssertionError("cross-boundary node reference was not rejected")

    merge_case = sample_workflow()
    merge_case["nodes"].extend([
        {"id": "n5", "name": "Side", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [250, 200], "parameters": {}},
        {"id": "n6", "name": "Join", "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [500, 100], "parameters": {}},
    ])
    merge_case["connections"] = {
        "Source": {"main": [[{"node": "Parse", "type": "main", "index": 0}], [{"node": "Side", "type": "main", "index": 0}]]},
        "Parse": {"main": [[{"node": "Join", "type": "main", "index": 0}]]},
        "Side": {"main": [[{"node": "Join", "type": "main", "index": 1}]]},
    }
    try:
        compile_replay(cfg, merge_case, "Parse", 0, "CASE-M", {}, connection_type="main")
    except ValueError:
        pass
    else:
        raise AssertionError("external incoming graph dependency was not rejected")

    with tempfile.TemporaryDirectory() as td:
        Path(td, "ok.txt").write_text("selftest", encoding="utf-8")
    print("PASS: offline selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
