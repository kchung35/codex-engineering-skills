#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
import secrets
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Set

from n8n_api import load_lab_config

REF_PATTERNS = [
    re.compile(r"\$node\[['\"]([^'\"]+)['\"]\]"),
    re.compile(r"\$\(['\"]([^'\"]+)['\"]\)"),
    re.compile(r"\$items\(['\"]([^'\"]+)['\"]"),
]

NODE_WRITABLE_KEYS = {
    "id", "name", "disabled", "notesInFlow", "notes", "type", "typeVersion",
    "executeOnce", "alwaysOutputData", "retryOnFail", "maxTries", "waitBetweenTries",
    "continueOnFail", "onError", "position", "parameters", "credentials", "customTelemetryTags",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def node_map(workflow):
    out = {}
    for node in workflow.get("nodes", []):
        name = node.get("name")
        if not name:
            raise ValueError("workflow contains a node without a name")
        if name in out:
            raise ValueError(f"duplicate node name: {name}")
        out[name] = node
    return out


def iter_edges(connections):
    """Yield (source, connection_type, output_index, target, target_input_index)."""
    for source, by_type in (connections or {}).items():
        if not isinstance(by_type, dict):
            continue
        for ctype, outputs in by_type.items():
            if not isinstance(outputs, list):
                continue
            for output_index, edges in enumerate(outputs):
                if not isinstance(edges, list):
                    continue
                for edge in edges:
                    if isinstance(edge, dict) and edge.get("node"):
                        yield source, ctype, output_index, edge["node"], int(edge.get("index", 0))


def selected_boundary_targets(connections, boundary, connection_type, output_index):
    try:
        outputs = connections[boundary][connection_type]
        edges = outputs[output_index]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"boundary {boundary!r} has no {connection_type!r} output index {output_index}")
    if not isinstance(edges, list):
        raise ValueError("selected boundary output is not a connection list")
    return copy.deepcopy(edges)


def descendants_from_targets(connections, initial_targets):
    adjacency: Dict[str, Set[str]] = {}
    for source, _ctype, _out, target, _in in iter_edges(connections):
        adjacency.setdefault(source, set()).add(target)
    seen: Set[str] = set()
    stack = [e.get("node") for e in initial_targets if isinstance(e, dict) and e.get("node")]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(adjacency.get(name, ()))
    return seen


def references_in_value(value: Any) -> Set[str]:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    refs: Set[str] = set()
    for pattern in REF_PATTERNS:
        refs.update(pattern.findall(text))
    return refs


def sanitize_node(node):
    return {k: copy.deepcopy(v) for k, v in node.items() if k in NODE_WRITABLE_KEYS}


def load_credential_map(path):
    if not path:
        return {}
    data = load_json(path)
    if data.get("schema_version") != 1 or not isinstance(data.get("credentials"), dict):
        raise ValueError("credential map must contain schema_version=1 and a credentials object")
    clean = {}
    forbidden_markers = {"password", "secret", "token", "key", "connectionString", "clientSecret"}
    for source_key, target in data["credentials"].items():
        if not isinstance(target, dict) or not target:
            raise ValueError(f"credential mapping {source_key!r} must be an object")
        extra = set(target) - {"id", "name"}
        if extra:
            raise ValueError(f"credential mapping {source_key!r} contains forbidden/unknown fields: {sorted(extra)}")
        if not target.get("id") and not target.get("name"):
            raise ValueError(f"credential mapping {source_key!r} needs id or name")
        for key in target:
            if key in forbidden_markers:
                raise ValueError(f"credential map may not contain secret field {key}")
        clean[str(source_key)] = {k: str(v) for k, v in target.items() if v is not None}
    return clean


def remap_credentials(node, policy, cred_map):
    credentials = node.get("credentials")
    if not credentials:
        return [], []
    if not isinstance(credentials, dict):
        raise ValueError(f"node {node['name']!r} has malformed credentials")
    remapped, missing = [], []
    for cred_type, ref in list(credentials.items()):
        if policy == "REUSE_REFERENCES":
            continue
        if not isinstance(ref, dict):
            missing.append(f"{node['name']}:{cred_type}")
            continue
        candidates = [str(ref.get("id", "")), str(ref.get("name", ""))]
        target = next((cred_map[c] for c in candidates if c and c in cred_map), None)
        if not target:
            missing.append(f"{node['name']}:{cred_type}:{ref.get('name') or ref.get('id')}")
            continue
        credentials[cred_type] = copy.deepcopy(target)
        remapped.append({
            "node": node["name"],
            "credential_type": cred_type,
            "source_reference": {k: ref.get(k) for k in ("id", "name") if ref.get(k) is not None},
            "lab_reference": copy.deepcopy(target),
        })
    return remapped, missing


def source_node_order(workflow):
    return [n.get("name") for n in workflow.get("nodes", []) if n.get("name")]


def compile_replay(cfg, source, boundary, output_index, case_id, credential_map,
                   preserve_static_data=False, connection_type="main"):
    if connection_type != "main":
        raise ValueError("BOUNDARY_REPLAY currently supports only the main connection type")
    nodes = node_map(source)
    if boundary not in nodes:
        raise ValueError(f"boundary node not found: {boundary!r}")
    connections = source.get("connections") or {}
    initial_edges = selected_boundary_targets(connections, boundary, connection_type, output_index)
    descendants = descendants_from_targets(connections, initial_edges)
    retained = {boundary} | descendants
    removed = set(nodes) - retained

    incoming_external = []
    for source_name, ctype, out_idx, target, in_idx in iter_edges(connections):
        if target in retained and target != boundary and source_name not in retained:
            incoming_external.append({
                "source": source_name, "target": target, "connection_type": ctype,
                "source_output_index": out_idx, "target_input_index": in_idx,
            })
    if incoming_external:
        detail = "; ".join(f"{x['source']} -> {x['target']}" for x in incoming_external[:8])
        raise ValueError(f"replay boundary has external incoming graph dependencies: {detail}")

    cross_refs = []
    for name in descendants:
        refs = references_in_value(nodes[name].get("parameters", {}))
        bad = sorted(refs & removed)
        if bad:
            cross_refs.append({"node": name, "removed_references": bad})
    if cross_refs:
        detail = "; ".join(f"{x['node']} -> {','.join(x['removed_references'])}" for x in cross_refs[:8])
        raise ValueError(f"retained nodes reference removed upstream nodes: {detail}")

    retained_nodes = []
    boundary_source = nodes[boundary]
    webhook_node_name = "LAB Fixture Trigger"
    if webhook_node_name in retained:
        raise ValueError(f"source workflow already contains reserved node name {webhook_node_name!r}")

    webhook_path = "__codex_lab/" + secrets.token_urlsafe(24)
    versions = cfg.get("node_type_versions") or {}
    webhook_version = float(versions.get("webhook", 2.1))
    code_version = float(versions.get("code", 2))
    position = boundary_source.get("position") or [0, 0]
    if not (isinstance(position, list) and len(position) >= 2):
        position = [0, 0]

    webhook = {
        "id": str(uuid.uuid4()), "name": webhook_node_name,
        "type": "n8n-nodes-base.webhook", "typeVersion": webhook_version,
        "position": [position[0] - 500, position[1]],
        "parameters": {"httpMethod": "POST", "path": webhook_path, "responseMode": "onReceived", "options": {}},
    }
    retained_nodes.append(webhook)

    injector = {
        "id": boundary_source.get("id") or str(uuid.uuid4()),
        "name": boundary, "type": "n8n-nodes-base.code", "typeVersion": code_version,
        "position": copy.deepcopy(position),
        "parameters": {
            "mode": "runOnceForAllItems",
            "jsCode": (
                "const body = $json.body ?? {};\n"
                "if (!Array.isArray(body.items)) { throw new Error('LAB fixture body.items must be an array'); }\n"
                "for (let i = 0; i < body.items.length; i++) {\n"
                "  const item = body.items[i];\n"
                "  if (!item || typeof item !== 'object' || Array.isArray(item) || !item.json || typeof item.json !== 'object' || Array.isArray(item.json)) {\n"
                "    throw new Error(`LAB fixture item ${i} must contain a json object`);\n"
                "  }\n"
                "}\n"
                "return body.items;"
            ),
        },
    }
    retained_nodes.append(injector)

    cred_policy = cfg.get("credential_reference_policy", "REQUIRE_MAP")
    all_remaps, missing = [], []
    for name in source_node_order(source):
        if name not in descendants:
            continue
        node = sanitize_node(nodes[name])
        remaps, node_missing = remap_credentials(node, cred_policy, credential_map)
        all_remaps.extend(remaps)
        missing.extend(node_missing)
        retained_nodes.append(node)
    if missing:
        raise ValueError("unmapped credential references under REQUIRE_MAP: " + "; ".join(missing))

    new_connections: Dict[str, Any] = {
        webhook_node_name: {"main": [[{"node": boundary, "type": "main", "index": 0}]]},
        boundary: {"main": [copy.deepcopy(initial_edges)]},
    }
    for source_name, by_type in connections.items():
        if source_name not in descendants:
            continue
        clean_by_type = {}
        for ctype, outputs in by_type.items():
            if not isinstance(outputs, list):
                continue
            clean_outputs = []
            for edges in outputs:
                if not isinstance(edges, list):
                    clean_outputs.append([])
                    continue
                clean_edges = [copy.deepcopy(e) for e in edges if isinstance(e, dict) and e.get("node") in retained]
                clean_outputs.append(clean_edges)
            clean_by_type[ctype] = clean_outputs
        if clean_by_type:
            new_connections[source_name] = clean_by_type

    settings = copy.deepcopy(source.get("settings") or {})
    for key in ("errorWorkflow", "binaryMode", "credentialResolverId"):
        settings.pop(key, None)
    settings["saveDataErrorExecution"] = "all"
    settings["saveDataSuccessExecution"] = "all"
    if "lab_execution_redaction_policy" in cfg:
        settings["redactionPolicy"] = cfg["lab_execution_redaction_policy"]

    prefix = cfg.get("workflow_name_prefix", "LAB__")
    source_name = source.get("name") or "workflow"
    lab_name = f"{prefix}{case_id}__{source_name}"
    if len(lab_name) > 128:
        lab_name = lab_name[:128]

    workflow = {"name": lab_name, "nodes": retained_nodes, "connections": new_connections, "settings": settings}
    if cfg.get("project_id"):
        workflow["projectId"] = cfg["project_id"]
    if preserve_static_data and source.get("staticData") is not None:
        workflow["staticData"] = copy.deepcopy(source["staticData"])

    meta = {
        "schema_version": 1, "case_id": case_id,
        "source_workflow_id": source.get("id"), "source_workflow_version_id": source.get("versionId"),
        "source_workflow_name": source_name, "strategy": "BOUNDARY_REPLAY",
        "boundary": {"node": boundary, "connection_type": connection_type, "output_index": output_index},
        "webhook_node": webhook_node_name, "webhook_path": webhook_path,
        "retained_nodes": [n["name"] for n in retained_nodes],
        "removed_nodes": [n for n in source_node_order(source) if n in removed],
        "credential_remaps": all_remaps,
        "static_data_preserved": bool(preserve_static_data and source.get("staticData") is not None),
        "semantic_limitations": [
            "Boundary implementation is bypassed and replaced by fixture injection.",
            "Full upstream paired-item ancestry is not reproduced.",
            "Only the selected boundary output index is replayed.",
        ],
    }
    return workflow, meta


def main():
    p = argparse.ArgumentParser(description="Compile an isolated n8n downstream replay workflow")
    p.add_argument("--config", required=True)
    p.add_argument("--source-workflow", required=True)
    p.add_argument("--boundary", required=True)
    p.add_argument("--connection-type", default="main")
    p.add_argument("--output-index", type=int, default=0)
    p.add_argument("--case-id", required=True)
    p.add_argument("--credential-map")
    p.add_argument("--preserve-static-data", action="store_true")
    p.add_argument("--out", required=True)
    p.add_argument("--meta-out", required=True)
    args = p.parse_args()
    try:
        cfg = load_lab_config(args.config)
        source = load_json(args.source_workflow)
        cred_map = load_credential_map(args.credential_map)
        workflow, meta = compile_replay(
            cfg, source, args.boundary, args.output_index, args.case_id, cred_map,
            preserve_static_data=args.preserve_static_data, connection_type=args.connection_type,
        )
        dump_json(workflow, args.out)
        dump_json(meta, args.meta_out)
        print(f"WROTE: {args.out} retained={len(workflow['nodes'])} removed={len(meta['removed_nodes'])}")
        print(f"WEBHOOK_PATH: {meta['webhook_path']}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
