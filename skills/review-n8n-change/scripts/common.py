#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

VOLATILE_TOP_LEVEL = {
    "active", "activeVersion", "activeVersionId", "createdAt", "updatedAt",
    "isArchived", "versionId", "versionCounter", "shared", "tags", "meta",
    "triggerCount", "sourceWorkflowId",
}
NON_BEHAVIORAL_TOP_LEVEL = VOLATILE_TOP_LEVEL | {"id", "name", "description", "nodeGroups"}
VOLATILE_NODE_FIELDS = {"createdAt", "updatedAt"}
NON_BEHAVIORAL_NODE_FIELDS = VOLATILE_NODE_FIELDS | {"position", "notes", "notesInFlow"}
NON_BEHAVIORAL_SETTINGS = {"timeSavedMode", "timeSavedPerExecution", "customTelemetryTags"}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(value: Any, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def resolve_path(base_file: str | Path, value: str | None) -> Path | None:
    if value is None:
        return None
    p = Path(value)
    if not p.is_absolute():
        p = Path(base_file).resolve().parent / p
    return p.resolve()


def artifact_view(workflow: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in workflow.items() if k not in VOLATILE_TOP_LEVEL}
    nodes = []
    for node in out.get("nodes", []) or []:
        if isinstance(node, dict):
            nodes.append({k: v for k, v in node.items() if k not in VOLATILE_NODE_FIELDS})
        else:
            nodes.append(node)
    out["nodes"] = nodes
    return out


def behavior_view(workflow: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in workflow.items() if k not in NON_BEHAVIORAL_TOP_LEVEL}
    nodes = []
    for node in workflow.get("nodes", []) or []:
        if not isinstance(node, dict):
            nodes.append(node)
            continue
        item = {k: v for k, v in node.items() if k not in NON_BEHAVIORAL_NODE_FIELDS}
        nodes.append(item)
    nodes.sort(key=lambda n: (str(n.get("id", "")), str(n.get("name", ""))) if isinstance(n, dict) else ("", str(n)))
    out["nodes"] = nodes
    settings = out.get("settings")
    if isinstance(settings, dict):
        out["settings"] = {k: v for k, v in settings.items() if k not in NON_BEHAVIORAL_SETTINGS}
    return out


def workflow_fingerprints(workflow: dict[str, Any]) -> dict[str, str]:
    return {
        "behavior_sha256": sha256_value(behavior_view(workflow)),
        "artifact_sha256": sha256_value(artifact_view(workflow)),
    }


def node_key(node: dict[str, Any]) -> str:
    nid = node.get("id")
    if nid:
        return f"id:{nid}"
    return f"name:{node.get('name', '')}"


def sanitized_node(node: dict[str, Any], *, behavioral: bool = True) -> dict[str, Any]:
    excluded = NON_BEHAVIORAL_NODE_FIELDS if behavioral else VOLATILE_NODE_FIELDS
    return {k: v for k, v in node.items() if k not in excluded}


def diff_paths(a: Any, b: Any, prefix: str = "") -> list[str]:
    if type(a) is not type(b):
        return [prefix or "$"]
    if isinstance(a, dict):
        paths: list[str] = []
        for key in sorted(set(a) | set(b)):
            p = f"{prefix}.{key}" if prefix else str(key)
            if key not in a or key not in b:
                paths.append(p)
            else:
                paths.extend(diff_paths(a[key], b[key], p))
        return paths
    if isinstance(a, list):
        return [] if a == b else [prefix or "$"]
    return [] if a == b else [prefix or "$"]
