#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse

from n8n_api import client_from_config, load_lab_config, normalize_instance_base_url


def validate_config(cfg):
    errors = []
    warnings = []
    if cfg.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if cfg.get("environment_class") != "NON_PRODUCTION":
        errors.append("environment_class must equal NON_PRODUCTION")
    try:
        base = normalize_instance_base_url(cfg.get("instance_base_url", ""))
        parsed = urllib.parse.urlparse(base)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" and host not in {"localhost", "127.0.0.1", "::1"}:
            errors.append("instance_base_url must use https except for localhost")
        denies = cfg.get("production_deny_hosts", [])
        if not isinstance(denies, list) or any(not isinstance(x, str) or not x.strip() for x in denies):
            errors.append("production_deny_hosts must be an array of non-empty host strings")
            denies = []
        for denied in denies:
            denied_host = str(denied).strip().lower()
            if denied_host and (host == denied_host or host.endswith("." + denied_host)):
                errors.append(f"instance host {host!r} matches production_deny_hosts entry {denied_host!r}")
    except Exception as exc:
        errors.append(str(exc))

    webhook = cfg.get("webhook_base_url")
    if not webhook:
        errors.append("webhook_base_url is required")
    else:
        try:
            wp = urllib.parse.urlparse(webhook.rstrip("/"))
            webhook_host = (wp.hostname or "").lower()
            if not wp.scheme or not wp.netloc:
                errors.append("webhook_base_url is invalid")
            elif wp.scheme != "https" and webhook_host not in {"localhost", "127.0.0.1", "::1"}:
                errors.append("webhook_base_url must use https except for localhost")
            for denied in cfg.get("production_deny_hosts", []) if isinstance(cfg.get("production_deny_hosts", []), list) else []:
                denied_host = str(denied).strip().lower()
                if denied_host and (webhook_host == denied_host or webhook_host.endswith("." + denied_host)):
                    errors.append(f"webhook host {webhook_host!r} matches production_deny_hosts entry {denied_host!r}")
        except Exception:
            errors.append("webhook_base_url is invalid")

    prefix = cfg.get("workflow_name_prefix")
    if not isinstance(prefix, str) or not prefix.strip():
        errors.append("workflow_name_prefix must be a non-empty string")
    elif not prefix.upper().startswith("LAB"):
        warnings.append("workflow_name_prefix does not visibly begin with LAB")

    if cfg.get("credential_reference_policy") not in {"REQUIRE_MAP", "REUSE_REFERENCES"}:
        errors.append("credential_reference_policy must be REQUIRE_MAP or REUSE_REFERENCES")
    if cfg.get("allow_external_writes") not in {True, False}:
        errors.append("allow_external_writes must be boolean")

    allowed_targets = cfg.get("allowed_test_targets", [])
    if not isinstance(allowed_targets, list) or any(not isinstance(x, str) or not x.strip() for x in allowed_targets):
        errors.append("allowed_test_targets must be an array of non-empty strings")
    elif len(allowed_targets) != len(set(allowed_targets)):
        errors.append("allowed_test_targets must not contain duplicates")

    external_denies = cfg.get("external_deny_hosts", [])
    if not isinstance(external_denies, list) or any(not isinstance(x, str) or not x.strip() for x in external_denies):
        errors.append("external_deny_hosts must be an array of non-empty host strings")

    for key, default in [
        ("max_fixture_bytes", 1048576),
        ("max_cases_per_matrix", 25),
        ("max_run_seconds", 180),
        ("poll_interval_seconds", 1.5),
        ("api_timeout_seconds", 30),
        ("webhook_timeout_seconds", 30),
        ("max_webhook_response_bytes", 65536),
    ]:
        value = cfg.get(key, default)
        if not isinstance(value, (int, float)) or value <= 0:
            errors.append(f"{key} must be positive")
    if cfg.get("max_cases_per_matrix", 25) > 100:
        warnings.append("max_cases_per_matrix > 100 is unusually high")
    if cfg.get("execution_data_mode", "follow") not in {"follow", "redact", "reveal"}:
        errors.append("execution_data_mode must be follow, redact, or reveal")
    if cfg.get("max_fixture_bytes", 1048576) > 50 * 1024 * 1024:
        warnings.append("max_fixture_bytes exceeds 50 MiB; large fixtures can distort lab behavior")
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description="Fail-closed n8n lab configuration preflight")
    p.add_argument("--config", required=True)
    p.add_argument("--live", action="store_true", help="also make a read-only API request")
    args = p.parse_args()

    cfg = load_lab_config(args.config)
    errors, warnings = validate_config(cfg)
    for w in warnings:
        print(f"WARN: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if not os.getenv("N8N_LAB_API_KEY"):
        print("ERROR: N8N_LAB_API_KEY is not set", file=sys.stderr)
        return 2

    if args.live:
        try:
            client = client_from_config(args.config)
            result = client.list_workflows(limit=1, project_id=cfg.get("project_id"))
            if not isinstance(result, dict):
                raise ValueError("unexpected response shape from GET /workflows")
        except Exception as exc:
            print(f"ERROR: read-only API preflight failed: {exc}", file=sys.stderr)
            return 2

    print("PASS: lab preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
