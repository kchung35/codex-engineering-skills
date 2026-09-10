#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from typing import Any

from common import artifact_view, behavior_view, diff_paths, load_json, node_key, sanitized_node, workflow_fingerprints, write_json


def map_nodes(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node in workflow.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        key = node_key(node)
        if key in result:
            raise ValueError(f"duplicate node identity: {key}")
        result[key] = node
    return result


def build_diff(source: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_fp = workflow_fingerprints(candidate)
    if source is None:
        return {
            "schema_version": 1,
            "mode": "NEW",
            "source_fingerprint": None,
            "candidate_fingerprint": candidate_fp,
            "behavioral_changed": True,
            "display_or_metadata_only": False,
            "nodes": {
                "added": [
                    {"key": node_key(node), "name": node.get("name"), "type": node.get("type")}
                    for node in candidate.get("nodes", []) or [] if isinstance(node, dict)
                ],
                "removed": [],
                "modified": [],
            },
            "connections_changed": bool(candidate.get("connections")),
            "settings_changed": sorted((candidate.get("settings") or {}).keys()) if isinstance(candidate.get("settings"), dict) else [],
            "static_data_changed": candidate.get("staticData") not in (None, {}, ""),
            "pin_data_changed": candidate.get("pinData") not in (None, {}, ""),
        }

    source_fp = workflow_fingerprints(source)
    source_nodes = map_nodes(source)
    candidate_nodes = map_nodes(candidate)
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []

    for key in sorted(set(candidate_nodes) - set(source_nodes)):
        node = candidate_nodes[key]
        added.append({"key": key, "name": node.get("name"), "type": node.get("type")})
    for key in sorted(set(source_nodes) - set(candidate_nodes)):
        node = source_nodes[key]
        removed.append({"key": key, "name": node.get("name"), "type": node.get("type")})
    for key in sorted(set(source_nodes) & set(candidate_nodes)):
        before = sanitized_node(source_nodes[key], behavioral=True)
        after = sanitized_node(candidate_nodes[key], behavioral=True)
        if before != after:
            modified.append({
                "key": key,
                "name_before": source_nodes[key].get("name"),
                "name_after": candidate_nodes[key].get("name"),
                "type_before": source_nodes[key].get("type"),
                "type_after": candidate_nodes[key].get("type"),
                "changed_fields": diff_paths(before, after),
            })

    source_settings = source.get("settings") if isinstance(source.get("settings"), dict) else {}
    candidate_settings = candidate.get("settings") if isinstance(candidate.get("settings"), dict) else {}
    settings_changed = [
        key for key in sorted(set(source_settings) | set(candidate_settings))
        if source_settings.get(key) != candidate_settings.get(key)
    ]
    behavioral_changed = behavior_view(source) != behavior_view(candidate)
    artifact_changed = artifact_view(source) != artifact_view(candidate)

    return {
        "schema_version": 1,
        "mode": "MODIFY",
        "source_fingerprint": source_fp,
        "candidate_fingerprint": candidate_fp,
        "behavioral_changed": behavioral_changed,
        "display_or_metadata_only": artifact_changed and not behavioral_changed,
        "nodes": {"added": added, "removed": removed, "modified": modified},
        "connections_changed": source.get("connections") != candidate.get("connections"),
        "settings_changed": settings_changed,
        "static_data_changed": source.get("staticData") != candidate.get("staticData"),
        "pin_data_changed": source.get("pinData") != candidate.get("pinData"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a semantic n8n workflow diff for review")
    parser.add_argument("--source")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        candidate = load_json(args.candidate)
        source = load_json(args.source) if args.source else None
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be a JSON object")
        if source is not None and not isinstance(source, dict):
            raise ValueError("source must be a JSON object")
        result = build_diff(source, candidate)
        write_json(result, args.out)
        print(f"behavioral_changed={str(result['behavioral_changed']).lower()}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
