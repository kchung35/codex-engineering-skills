from __future__ import annotations
import json, os, time, urllib.error, urllib.parse, urllib.request

class N8NError(RuntimeError):
    pass

class N8NClient:
    def __init__(self, base_url, api_key_env, timeout=20):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise N8NError(f"Missing API key environment variable: {api_key_env}")

    def request(self, method, path, body=None, query=None):
        url = self.base_url + "/api/v1" + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-N8N-API-KEY", self.api_key)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            raise N8NError(f"HTTP {e.code} {method} {path}: {raw[:2000]}") from e
        except urllib.error.URLError as e:
            raise N8NError(f"Network error {method} {path}: {e}") from e

    def get_workflow(self, workflow_id):
        return self.request("GET", f"/workflows/{workflow_id}")

    def update_workflow_draft(self, workflow_id, payload):
        return self.request("PUT", f"/workflows/{workflow_id}", payload, {"publishIfActive": "false"})

    def publish_version(self, workflow_id, version_id):
        return self.request("POST", f"/workflows/{workflow_id}/activate", {"versionId": version_id})

    def unpublish(self, workflow_id):
        return self.request("POST", f"/workflows/{workflow_id}/deactivate")

    def list_executions(self, workflow_id, limit=20):
        return self.request("GET", "/executions", query={"workflowId": workflow_id, "limit": str(limit)})

    def wait_active_version(self, workflow_id, expected_version_id, timeout_seconds, poll_interval=2):
        end = time.monotonic() + timeout_seconds
        last = None
        while time.monotonic() < end:
            last = self.get_workflow(workflow_id)
            if last.get("activeVersionId") == expected_version_id:
                return last
            time.sleep(poll_interval)
        raise N8NError(f"Timed out waiting for activeVersionId={expected_version_id}; observed={None if last is None else last.get('activeVersionId')}")

    def wait_unpublished(self, workflow_id, timeout_seconds, poll_interval=2):
        end = time.monotonic() + timeout_seconds
        last = None
        while time.monotonic() < end:
            last = self.get_workflow(workflow_id)
            if last.get("activeVersionId") in (None, ""):
                return last
            time.sleep(poll_interval)
        raise N8NError(f"Timed out waiting for unpublish; observed={None if last is None else last.get('activeVersionId')}")
