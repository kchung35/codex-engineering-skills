# Test plan contract

A live laboratory run starts from a machine-readable plan. The plan captures intent before mechanics so the harness cannot silently change the question while testing.

## Envelope

```json
{
  "schema_version": 1,
  "test_id": "CASE-017-E03",
  "question": "Does the Normalize Holdings fix preserve five canonical holdings when sector is null?",
  "strategy": "BOUNDARY_REPLAY",
  "source": {
    "workflow_snapshot": "artifacts/source-workflow.json",
    "workflow_id": "source-workflow-id",
    "workflow_version_id": "source-version-id"
  },
  "boundary": {
    "node": "Extract Holdings",
    "connection_type": "main",
    "output_index": 0
  },
  "cases": [
    {
      "id": "historical-failure",
      "fixture": "fixtures/failing.json",
      "assertions": "assertions/failing.json"
    }
  ],
  "side_effect_manifest": "side-effects.json",
  "credential_map": "credential-map.json",
  "comparison_baseline": "artifacts/baseline-execution.json",
  "timeout_seconds": 120,
  "cleanup_policy": "DELETE"
}
```

## Required properties

Every plan requires:

- `schema_version: 1`;
- non-empty `test_id` and `question`;
- one strategy from `BOUNDARY_REPLAY`, `RETRY_IN_LAB`, `NATIVE_TRIGGER_LAB`, or `SNAPSHOT_ONLY`;
- positive `timeout_seconds` no greater than the lab-configured `max_run_seconds`;
- `cleanup_policy` of `DELETE` or `KEEP_FOR_INSPECTION`.

`BOUNDARY_REPLAY` additionally requires:

- a source workflow snapshot;
- boundary node, `main` connection type, and non-negative output index;
- at least one case, each with a unique ID, fixture path, and assertion path;
- a side-effect manifest;
- a credential map when the lab policy is `REQUIRE_MAP` and retained nodes need credentials.

`RETRY_IN_LAB` requires a lab execution ID and side-effect manifest.

`NATIVE_TRIGGER_LAB` requires an explicit adapter/runbook identifier, side-effect manifest, and at least one deterministic assertion set. Project-specific adapters own event generation.

`SNAPSHOT_ONLY` requires at least one source identifier or snapshot target and must not claim execution verification.

## Intent immutability

Once a live run begins, do not change the test question, fixture, assertions, or boundary in place. If evidence requires a different experiment, create a new plan/test ID. This keeps failed attempts auditable rather than retroactively redefining success.

## Path discipline

Paths in plans should be relative to the plan file where practical. Generated execution artifacts and deployment receipts belong in ignored case-artifact directories, not the skill repository itself.
