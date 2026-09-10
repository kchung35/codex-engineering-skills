from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

READ_ONLY_KEYS = {
    "id", "active", "activeVersion", "activeVersionId", "createdAt", "updatedAt",
    "isArchived", "versionId", "versionCounter", "triggerCount", "shared", "tags", "meta"
}
NODE_EDITOR_ONLY_KEYS = {"position", "notes", "notesInFlow", "createdAt", "updatedAt"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_workflow(workflow):
    w = copy.deepcopy(workflow)
    for k in list(w):
        if k in READ_ONLY_KEYS:
            w.pop(k, None)
    for node in w.get("nodes", []):
        for k in NODE_EDITOR_ONLY_KEYS:
            node.pop(k, None)
    return w


def fingerprint(workflow):
    payload = json.dumps(canonical_workflow(workflow), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sanitized_update_payload(workflow):
    w = canonical_workflow(workflow)
    allowed = {"name", "nodes", "connections", "settings", "staticData", "pinData", "nodeGroups", "description", "parentFolderId"}
    return {k: v for k, v in w.items() if k in allowed}
