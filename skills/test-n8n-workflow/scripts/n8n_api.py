#!/usr/bin/env python3
"""Minimal n8n public API client used by the test-n8n-workflow skill.

No third-party dependencies. API keys are read from N8N_LAB_API_KEY unless
explicitly supplied to N8NClient by code. This module intentionally exposes
only operations needed by the lab harness.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class N8NAPIError(RuntimeError):
    def __init__(self, method: str, url: str, status: Optional[int], message: str):
        super().__init__(f"{method} {url} -> {status or 'transport-error'}: {message}")
        self.method = method
        self.url = url
        self.status = status
        self.message = message


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dump_json(obj: Any, path: str | Path | None = None) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def normalize_instance_base_url(url: str) -> str:
    value = url.strip().rstrip("/")
    if value.endswith("/api/v1"):
        value = value[: -len("/api/v1")]
    parsed = urllib.parse.urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid instance_base_url: {url!r}")
    return value


def api_root(instance_base_url: str) -> str:
    return normalize_instance_base_url(instance_base_url) + "/api/v1"


@dataclass
class N8NClient:
    instance_base_url: str
    api_key: str
    timeout: float = 30.0

    def __post_init__(self) -> None:
        self.instance_base_url = normalize_instance_base_url(self.instance_base_url)
        if not self.api_key:
            raise ValueError("n8n API key is empty")

    @property
    def root(self) -> str:
        return self.instance_base_url + "/api/v1"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Any = None,
        timeout: Optional[float] = None,
    ) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        url = self.root + path
        if params:
            clean = {k: str(v).lower() if isinstance(v, bool) else str(v)
                     for k, v in params.items() if v is not None}
            url += "?" + urllib.parse.urlencode(clean)
        payload = None
        headers = {
            "Accept": "application/json",
            "X-N8N-API-KEY": self.api_key,
            "User-Agent": "codex-test-n8n-workflow/1",
        }
        if body is not None:
            payload = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=payload, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                raw = resp.read()
                if not raw:
                    return None
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype.lower() or raw[:1] in (b"{", b"["):
                    return json.loads(raw.decode("utf-8"))
                return raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read(4096)
            text = raw.decode("utf-8", errors="replace")
            # Do not dump arbitrarily large response bodies; they may contain execution data.
            raise N8NAPIError(method.upper(), url, exc.code, text[:2000]) from None
        except urllib.error.URLError as exc:
            raise N8NAPIError(method.upper(), url, None, str(exc.reason)) from None

    def list_workflows(self, *, limit: int = 20, cursor: str | None = None,
                       project_id: str | None = None) -> Any:
        params: Dict[str, Any] = {"limit": limit, "cursor": cursor, "projectId": project_id}
        return self.request("GET", "/workflows", params=params)

    def get_workflow(self, workflow_id: str, *, exclude_pinned_data: bool = True) -> Any:
        return self.request("GET", f"/workflows/{urllib.parse.quote(str(workflow_id), safe='')}",
                            params={"excludePinnedData": exclude_pinned_data})

    def create_workflow(self, workflow: Dict[str, Any]) -> Any:
        return self.request("POST", "/workflows", body=workflow)

    def publish_workflow(self, workflow_id: str, *, version_id: str | None = None) -> Any:
        body: Dict[str, Any] = {}
        if version_id:
            body["versionId"] = version_id
        return self.request("POST", f"/workflows/{urllib.parse.quote(str(workflow_id), safe='')}/publish",
                            body=body)

    def unpublish_workflow(self, workflow_id: str) -> Any:
        return self.request("POST", f"/workflows/{urllib.parse.quote(str(workflow_id), safe='')}/unpublish",
                            body={})

    def delete_workflow(self, workflow_id: str) -> Any:
        return self.request("DELETE", f"/workflows/{urllib.parse.quote(str(workflow_id), safe='')}")

    def list_executions(
        self,
        *,
        workflow_id: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        include_data: bool = False,
        redact: str = "follow",
    ) -> Any:
        params: Dict[str, Any] = {
            "workflowId": workflow_id,
            "projectId": project_id,
            "status": status,
            "startedAfter": started_after,
            "startedBefore": started_before,
            "limit": limit,
            "cursor": cursor,
            "includeData": include_data,
        }
        if redact == "redact":
            params["redactExecutionData"] = True
        elif redact == "reveal":
            if os.getenv("N8N_ALLOW_REVEAL_EXECUTION_DATA") != "YES":
                raise ValueError("Reveal requested but N8N_ALLOW_REVEAL_EXECUTION_DATA=YES is not set")
            params["redactExecutionData"] = False
        elif redact != "follow":
            raise ValueError("redact must be one of: follow, redact, reveal")
        return self.request("GET", "/executions", params=params)

    def get_execution(
        self,
        execution_id: str,
        *,
        include_data: bool = True,
        ignore_data_size_limit: bool = False,
        redact: str = "follow",
    ) -> Any:
        params: Dict[str, Any] = {
            "includeData": include_data,
            "ignoreDataSizeLimit": ignore_data_size_limit,
        }
        if redact == "redact":
            params["redactExecutionData"] = True
        elif redact == "reveal":
            if os.getenv("N8N_ALLOW_REVEAL_EXECUTION_DATA") != "YES":
                raise ValueError("Reveal requested but N8N_ALLOW_REVEAL_EXECUTION_DATA=YES is not set")
            params["redactExecutionData"] = False
        elif redact != "follow":
            raise ValueError("redact must be one of: follow, redact, reveal")
        return self.request("GET", f"/executions/{urllib.parse.quote(str(execution_id), safe='')}",
                            params=params)

    def retry_execution(self, execution_id: str, *, load_workflow: bool = False) -> Any:
        return self.request("POST", f"/executions/{urllib.parse.quote(str(execution_id), safe='')}/retry",
                            body={"loadWorkflow": bool(load_workflow)})


def load_lab_config(path: str | Path) -> Dict[str, Any]:
    cfg = _load_json(path)
    if not isinstance(cfg, dict):
        raise ValueError("Lab config must be a JSON object")
    return cfg


def client_from_config(config_path: str | Path) -> N8NClient:
    cfg = load_lab_config(config_path)
    key = os.getenv("N8N_LAB_API_KEY", "")
    if not key:
        raise ValueError("N8N_LAB_API_KEY is not set")
    return N8NClient(cfg["instance_base_url"], key,
                     timeout=float(cfg.get("api_timeout_seconds", 30)))


def _cli() -> int:
    p = argparse.ArgumentParser(description="Minimal n8n public API client for the lab harness")
    p.add_argument("--config", required=True)
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("get-workflow")
    g.add_argument("id")
    g.add_argument("--include-pinned-data", action="store_true")
    g.add_argument("--out")

    lw = sub.add_parser("list-workflows")
    lw.add_argument("--limit", type=int, default=20)
    lw.add_argument("--out")

    ge = sub.add_parser("get-execution")
    ge.add_argument("id")
    ge.add_argument("--redact", choices=["follow", "redact", "reveal"], default="follow")
    ge.add_argument("--ignore-data-size-limit", action="store_true")
    ge.add_argument("--out")

    le = sub.add_parser("list-executions")
    le.add_argument("--workflow-id")
    le.add_argument("--limit", type=int, default=20)
    le.add_argument("--out")

    args = p.parse_args()
    client = client_from_config(args.config)

    if args.command == "get-workflow":
        result = client.get_workflow(args.id, exclude_pinned_data=not args.include_pinned_data)
    elif args.command == "list-workflows":
        result = client.list_workflows(limit=args.limit)
    elif args.command == "get-execution":
        result = client.get_execution(args.id, redact=args.redact,
                                      ignore_data_size_limit=args.ignore_data_size_limit)
    elif args.command == "list-executions":
        result = client.list_executions(workflow_id=args.workflow_id, limit=args.limit)
    else:
        raise AssertionError(args.command)
    _dump_json(result, getattr(args, "out", None))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_cli())
    except (N8NAPIError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
