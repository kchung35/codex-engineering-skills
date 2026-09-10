#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab_preflight import validate_config
from n8n_api import N8NAPIError, client_from_config, load_lab_config, normalize_instance_base_url
from validate_lab_workflow import validate_workflow


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require_preflight(cfg):
    errors, warnings = validate_config(cfg)
    if errors:
        raise ValueError("lab preflight failed: " + "; ".join(errors))
    return warnings


def workflow_semantic_hash(workflow):
    if not isinstance(workflow, dict):
        raise ValueError("workflow must be an object")
    core = {
        "name": workflow.get("name"),
        "nodes": workflow.get("nodes") or [],
        "connections": workflow.get("connections") or {},
        "settings": workflow.get("settings") or {},
        "staticData": workflow.get("staticData"),
    }
    raw = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def safe_rollback(client, workflow_id: str | None, expected_name: str, prefix: str):
    if not workflow_id:
        return {"attempted": False, "deleted": False, "errors": []}
    result = {"attempted": True, "deleted": False, "errors": []}
    try:
        current = client.get_workflow(workflow_id)
    except N8NAPIError as exc:
        if exc.status == 404:
            result["deleted"] = True
            return result
        result["errors"].append(f"identity check failed: {exc}")
        return result
    current_name = current.get("name") if isinstance(current, dict) else None
    if current_name != expected_name or not str(current_name or "").startswith(prefix):
        result["errors"].append(f"refusing rollback: workflow identity mismatch id={workflow_id!r} name={current_name!r}")
        return result
    try:
        client.unpublish_workflow(workflow_id)
    except N8NAPIError as exc:
        if exc.status not in {400, 404, 409}:
            result["errors"].append(f"unpublish failed: {exc}")
    try:
        client.delete_workflow(workflow_id)
        result["deleted"] = True
    except N8NAPIError as exc:
        if exc.status == 404:
            result["deleted"] = True
        else:
            result["errors"].append(f"delete failed: {exc}")
    return result


def deploy(config_path, workflow_path, side_effects_path, meta_path, out_path, *, ack_writes=False):
    cfg = load_lab_config(config_path)
    require_preflight(cfg)
    workflow = load_json(workflow_path)
    manifest = load_json(side_effects_path)
    meta = load_json(meta_path)
    errors, warnings, classes = validate_workflow(cfg, workflow, manifest, ack_writes=ack_writes)
    if errors:
        raise ValueError("lab workflow safety gate failed: " + "; ".join(errors))
    if meta.get("schema_version") != 1 or meta.get("strategy") != "BOUNDARY_REPLAY":
        raise ValueError("lab meta must be schema_version=1 BOUNDARY_REPLAY metadata")
    expected_name = workflow.get("name")
    prefix = cfg.get("workflow_name_prefix", "LAB__")
    if not isinstance(expected_name, str) or not expected_name.startswith(prefix):
        raise ValueError("workflow name does not satisfy configured lab prefix")

    client = client_from_config(config_path)
    probe = client.list_workflows(limit=1, project_id=cfg.get("project_id"))
    if not isinstance(probe, dict):
        raise ValueError("unexpected response from read-only preflight")

    created_id = None
    try:
        created = client.create_workflow(workflow)
        if not isinstance(created, dict) or not created.get("id"):
            raise ValueError("POST /workflows returned no workflow id")
        created_id = str(created["id"])
        fetched = client.get_workflow(created_id)
        if not isinstance(fetched, dict) or fetched.get("name") != expected_name:
            raise ValueError("created workflow identity/name could not be verified")
        if not str(fetched.get("name", "")).startswith(prefix):
            raise ValueError("created workflow lost configured lab prefix")
        version_id = created.get("versionId") or fetched.get("versionId")
        published = client.publish_workflow(created_id, version_id=version_id)
        published_state = client.get_workflow(created_id)
        if not isinstance(published_state, dict) or published_state.get("name") != expected_name:
            raise ValueError("published workflow identity could not be re-verified")
        receipt = {
            "schema_version": 1,
            "environment_class": "NON_PRODUCTION",
            "instance_base_url": normalize_instance_base_url(cfg["instance_base_url"]),
            "webhook_base_url": str(cfg["webhook_base_url"]).rstrip("/"),
            "project_id": cfg.get("project_id"),
            "workflow_id": created_id,
            "workflow_name": expected_name,
            "workflow_version_id": ((published or {}).get("versionId") if isinstance(published, dict) else None) or version_id,
            "webhook_node": meta.get("webhook_node"),
            "webhook_path": meta.get("webhook_path"),
            "boundary": meta.get("boundary"),
            "workflow_semantic_sha256": workflow_semantic_hash(published_state),
            "case_id": meta.get("case_id"),
            "source_workflow_id": meta.get("source_workflow_id"),
            "source_workflow_version_id": meta.get("source_workflow_version_id"),
            "side_effect_gate": "PASS",
            "side_effect_classifications": classes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cleanup_required": True,
            "cleanup_status": "PENDING",
            "warnings": warnings,
        }
        if not receipt["webhook_path"]:
            raise ValueError("lab metadata has no webhook_path")
        dump_json(receipt, out_path)
        return receipt
    except Exception as exc:
        rollback = safe_rollback(client, created_id, expected_name, prefix)
        raise RuntimeError(f"deployment failed: {exc}; rollback={json.dumps(rollback, ensure_ascii=False)}") from exc


def main():
    p = argparse.ArgumentParser(description="Create and publish a validated ephemeral n8n lab workflow")
    p.add_argument("--config", required=True)
    p.add_argument("--workflow", required=True)
    p.add_argument("--side-effects", required=True)
    p.add_argument("--meta", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--ack-writes", action="store_true")
    args = p.parse_args()
    try:
        receipt = deploy(args.config, args.workflow, args.side_effects, args.meta, args.out, ack_writes=args.ack_writes)
        print(f"PASS: deployed lab workflow id={receipt['workflow_id']} name={receipt['workflow_name']!r}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
