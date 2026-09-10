#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from n8n_api import load_lab_config


def canonical_items_bytes(items):
    return json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_items(items):
    return hashlib.sha256(canonical_items_bytes(items)).hexdigest()


def validate_fixture(data, max_bytes=None):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["fixture must be a JSON object"], warnings
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    items = data.get("items")
    if not isinstance(items, list):
        errors.append("items must be an array")
        return errors, warnings
    if max_bytes is not None and len(canonical_items_bytes(items)) > max_bytes:
        errors.append(f"fixture items exceed max_fixture_bytes={max_bytes}")
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{i}] must be an object")
            continue
        if not isinstance(item.get("json"), dict):
            errors.append(f"items[{i}].json must be an object")
        if "binary" in item and item.get("binary"):
            errors.append(f"items[{i}] contains binary metadata; portable boundary replay is blocked")
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        errors.append("metadata must be an object")
    else:
        if not meta.get("fixture_id"):
            errors.append("metadata.fixture_id is required")
        if not meta.get("boundary_node"):
            errors.append("metadata.boundary_node is required")
        prov = meta.get("provenance")
        if not isinstance(prov, dict) or not prov.get("kind"):
            errors.append("metadata.provenance.kind is required")
        expected = meta.get("sha256")
        actual = digest_items(items)
        if not expected:
            warnings.append(f"metadata.sha256 missing; expected {actual}")
        elif expected != actual:
            errors.append(f"metadata.sha256 mismatch: expected {expected}, actual {actual}")
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description="Validate a boundary replay fixture")
    p.add_argument("fixture")
    p.add_argument("--config")
    args = p.parse_args()
    data = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    max_bytes = None
    if args.config:
        max_bytes = int(load_lab_config(args.config).get("max_fixture_bytes", 1048576))
    errors, warnings = validate_fixture(data, max_bytes=max_bytes)
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"PASS: fixture {data['metadata']['fixture_id']} sha256={digest_items(data['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
