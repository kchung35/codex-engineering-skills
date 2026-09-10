---
name: test-n8n-workflow
description: "Run controlled, reproducible tests against n8n workflows in a dedicated non-production lab. Use when a debugging experiment, regression check, change verification, or historical failing case must be executed in real n8n rather than only locally. Safely snapshot workflows/executions, extract boundary fixtures, compile isolated replay clones, publish ephemeral lab workflows, trigger them, capture execution data, apply deterministic assertions, compare executions, and clean up. Do not use to experiment directly on production workflows or to diagnose root cause by itself."
---

# Test n8n Workflow

Operate as a deterministic laboratory for n8n. The skill's job is to execute an already-defined test safely and return high-quality evidence. It does not replace causal diagnosis, architecture design, or release approval.

Use the lifecycle:

`PREFLIGHT -> TEST_PLAN -> FIXTURE -> ISOLATE -> VALIDATE -> DEPLOY_LAB -> EXECUTE -> CAPTURE -> ASSERT -> COMPARE -> CLEANUP -> REPORT`

## Non-negotiable rules

1. Test only against an explicitly configured `NON_PRODUCTION` n8n lab environment. Refuse mutating operations when lab preflight fails.
2. Never activate, update, retry, or delete a production workflow as part of testing.
3. Never copy or print plaintext credentials. Credential handling is reference remapping only; test credentials must already exist in the lab.
4. A green HTTP response is not a passing workflow test. Retrieve the resulting n8n execution and inspect its status and relevant node data.
5. Assertions must be deterministic. Do not use an LLM judgment as the pass/fail oracle for a regression test.
6. Preserve provenance: every fixture and execution result must identify the case, boundary, source, workflow/version, and environment where applicable.
7. Default to the smallest executable causal cone. Do not duplicate unrelated workflow branches into the lab merely because they exist in the source workflow.
8. Before any live run, classify every non-local node in the executable cone under the side-effect policy. Unknown nodes default to `DENY`.
9. External writes default to forbidden. `WRITE_ALLOWED` requires both policy-level permission and an explicit command acknowledgment.
10. Historical execution retry is allowed only when the execution belongs to the configured non-production lab and the executable workflow passes the same side-effect gate.
11. Do not silently weaken a test because the harness is inconvenient. If the chosen replay boundary cannot preserve required semantics, report the limitation and choose a different execution strategy.
12. Bound tests: payload size, number of cases, run duration, and polling duration must remain within the lab configuration.
13. Clean up ephemeral lab workflows after evidence is captured unless the test plan explicitly requires keeping them for inspection. Cleanup failure is a surfaced test-harness failure, never hidden.
14. Keep raw execution data out of source control. Store it under the debugging case or another ignored test-artifact directory.
15. If a live test exposes a new unexplained failure mechanism, return the evidence to `debug-n8n-workflow`; do not improvise a speculative patch inside this skill.

## 1. PREFLIGHT — prove this is a lab

A live test requires a lab configuration file. Start from the contract in `references/lab-safety-model.md`.

Minimum shape:

```json
{
  "schema_version": 1,
  "environment_class": "NON_PRODUCTION",
  "instance_base_url": "https://example-lab.app.n8n.cloud",
  "webhook_base_url": "https://example-lab.app.n8n.cloud",
  "project_id": "optional-project-id",
  "workflow_name_prefix": "LAB__",
  "credential_reference_policy": "REQUIRE_MAP",
  "allowed_test_targets": ["lab-postgres", "mock-api"],
  "allow_external_writes": false,
  "production_deny_hosts": ["n8n-prod.example.com"],
  "external_deny_hosts": ["api-prod.example.com"],
  "max_fixture_bytes": 1048576,
  "max_cases_per_matrix": 25,
  "max_run_seconds": 180
}
```

The API key must come from `N8N_LAB_API_KEY`, never from the config file.

Run:

```bash
python scripts/lab_preflight.py --config <lab-config.json> --live
```

Do not proceed with mutating operations unless this passes.

Prefer least-privilege API keys. For the full ephemeral-clone flow the lab typically needs workflow read/create/delete/publish/unpublish and execution list/read scopes. Add retry scope only when `RETRY_IN_LAB` is intentionally used. Read `references/n8n-api-current.md` for the current API contract captured by this skill.

## 2. TEST_PLAN — define what the run is supposed to prove

Before execution, write a machine-readable test plan using `assets/test-plan.example.json` as the seed. A plan must state:

- test/case identifier;
- question being tested;
- execution strategy;
- source workflow snapshot or lab workflow ID;
- replay boundary where applicable;
- fixture(s) and provenance;
- side-effect manifest;
- deterministic assertions;
- optional comparison baseline;
- timeout;
- cleanup policy.

The laboratory must not invent the causal question. If invoked from `debug-n8n-workflow`, use that investigation's experiment definition.

Validate the plan before doing live work:

```bash
python scripts/validate_test_plan.py --config <lab-config.json> --plan <test-plan.json>
```

Read `references/test-plan-contract.md` and `references/execution-strategies.md`, then choose exactly one primary strategy.

### Strategy A — `BOUNDARY_REPLAY` (default for most debugging)

Replay the captured output of a stable node boundary into the downstream portion of a workflow on the lab instance.

Use when:

- the suspected failure is downstream of a known boundary;
- exact historical or synthetic boundary output can be represented as n8n items;
- trigger behavior itself is not under test;
- downstream expressions do not require removed upstream execution state.

### Strategy B — `RETRY_IN_LAB`

Retry an existing failed execution that already occurred on a harness-created workflow in the configured non-production lab.

The safe wrapper validates the current `LAB__` workflow and its side-effect manifest, then retries with `loadWorkflow=true` so the validated currently saved workflow is the version that executes. It deliberately does not expose arbitrary retry of a historical stored workflow.

```bash
python scripts/retry_lab_execution.py \
  --config <lab-config.json> \
  --execution-id <lab-execution-id> \
  --side-effects <side-effects.json> \
  --out <retry-receipt.json> \
  --execution-out <retry-execution.json>
```

Never use production retry as a convenient fixture mechanism.

### Strategy C — `NATIVE_TRIGGER_LAB`

Exercise the real trigger or integration against a dedicated lab instance and test account/system.

Use when the trigger, webhook/auth layer, polling behavior, scheduler, credential integration, or external event semantics are themselves causal.

This strategy usually needs project-specific adapters and test credentials. Do not pretend a boundary replay verifies trigger behavior.

### Strategy D — `SNAPSHOT_ONLY`

Capture current workflow/execution evidence without creating or running anything.

Use for read-only forensic comparison or when live mutation is not authorized.

## 3. FIXTURE — capture reproducible input

For `BOUNDARY_REPLAY`, prefer extracting an actual node output from a known execution:

```bash
python scripts/extract_fixture.py \
  --execution <execution.json> \
  --node "<boundary node>" \
  --run-index 0 \
  --output-index 0 \
  --out <fixture.json>
```

Then validate it:

```bash
python scripts/validate_fixture.py --config <lab-config.json> <fixture.json>
```

Fixtures use a strict envelope described in `references/fixture-contract.md`. Store an SHA-256 digest and provenance. Do not edit a historical fixture in place; create a new fixture with new provenance.

Binary data is not portable merely because binary metadata appears in execution JSON. If the test depends on actual binary content, use a strategy that provisions the referenced binary asset in the lab or exercise the native source. Read `references/fixture-contract.md`.

## 4. ISOLATE — compile the smallest faithful replay cone

For `BOUNDARY_REPLAY`, create an ephemeral lab workflow from the source workflow snapshot:

```bash
python scripts/make_replay_clone.py \
  --config <lab-config.json> \
  --source-workflow <workflow.json> \
  --boundary "<node name>" \
  --output-index 0 \
  --case-id <case-id> \
  --credential-map <credential-map.json> \
  --out <lab-workflow.json> \
  --meta-out <lab-meta.json>
```

The compiler must:

- retain only the selected boundary and nodes reachable downstream from the chosen output;
- replace the boundary implementation with a fixture injector **using the same node name and node ID**;
- add one high-entropy lab Webhook trigger;
- remove incoming edges into the replay boundary;
- remove unrelated upstream and side branches;
- remove external error-workflow linkage;
- reset workflow static state unless the plan explicitly requires preserving controlled state;
- strip source webhook identifiers;
- remap credential references according to lab policy;
- fail if retained nodes reference removed upstream nodes through cross-node expressions;
- emit metadata recording exactly what was removed, retained, remapped, and bypassed.

The same-name boundary replacement matters because downstream expressions may reference the boundary by node name. It does **not** make upstream references magically valid; cross-boundary dependencies remain a hard validation concern.

Read `references/replay-boundary-rules.md` before choosing a non-trivial boundary.

## 5. VALIDATE — prove the lab workflow is safe enough to execute

Create a side-effect manifest as described in `references/lab-safety-model.md`.

Then run:

```bash
python scripts/validate_lab_workflow.py \
  --config <lab-config.json> \
  --workflow <lab-workflow.json> \
  --side-effects <side-effects.json>
```

The validator treats a limited set of known local/control-flow nodes as intrinsically local. Every other retained node must be explicitly classified.

Allowed classifications:

- `LOCAL`
- `READ_ONLY`
- `TEST_TARGET`
- `STUBBED`
- `WRITE_ALLOWED`
- `DENY`

`TEST_TARGET` must name a target alias that is explicitly present in `allowed_test_targets`. `WRITE_ALLOWED` is blocked unless the lab config enables external writes and the caller passes the explicit acknowledgment required by the validator/deployer. Static HTTP destinations matching `external_deny_hosts` are rejected regardless of classification.

Do not label a node `READ_ONLY` merely because its name sounds read-only. Inspect the actual operation/method/query.

## 6. DEPLOY_LAB — create and publish only the ephemeral lab workflow

After validation:

```bash
python scripts/deploy_lab_clone.py \
  --config <lab-config.json> \
  --workflow <lab-workflow.json> \
  --side-effects <side-effects.json> \
  --meta <lab-meta.json> \
  --out <deployment.json>
```

The deployer performs preflight again, creates the workflow in the configured lab project, verifies the returned workflow identity/name, publishes it, re-fetches it, and records a semantic workflow hash in the deployment receipt. Every fixture trigger checks that hash again and refuses to execute a lab workflow that drifted after deployment.

If publication fails after creation, it attempts rollback by deleting the newly created lab workflow and reports any cleanup failure.

Why publish? n8n's automated Webhook production URL is registered for published workflows. The editor's test URL requires an interactive “listen for test event” state and is not the deterministic API surface used by this harness. Publishing is therefore allowed only because this is an explicitly non-production ephemeral lab workflow.

## 7. EXECUTE — one controlled invocation at a time

Trigger a single fixture:

```bash
python scripts/trigger_webhook.py \
  --config <lab-config.json> \
  --deployment <deployment.json> \
  --fixture <fixture.json> \
  --out <invocation.json>
```

Before invoking the Webhook, record the existing execution IDs for that lab workflow. This gives the harness a deterministic way to identify the new execution without relying only on synchronized clocks.

Then wait for and capture the resulting execution:

```bash
python scripts/wait_execution.py \
  --config <lab-config.json> \
  --deployment <deployment.json> \
  --invocation <invocation.json> \
  --out <execution.json>
```

The waiter must fail on ambiguous correlation rather than arbitrarily choosing one of multiple new executions.

Do not run concurrent cases against the same ephemeral replay workflow unless a concurrency test explicitly requires it. Serial execution is the default.

## 8. CAPTURE — retrieve actual n8n evidence

The n8n execution read API can include detailed execution data. Capture at least:

- execution ID;
- workflow ID and workflow version ID;
- execution mode;
- status;
- start/stop times;
- retry linkage if applicable;
- execution data required by the assertions;
- whether data was redacted or too large to display.

If execution data is redacted, do not silently convert missing values into test failures. Mark the evidence as insufficient and follow the configured data-access policy.

Default to following the lab workflow's redaction policy. Revealing explicitly redacted data requires both the n8n `execution:reveal` scope and an explicit local opt-in; it is not the default behavior of these scripts.

Read `references/execution-data-anatomy.md`.

## 9. ASSERT — test semantics, not vibes

Assertions are deterministic JSON rules. Example:

```json
{
  "schema_version": 1,
  "assertions": [
    {"type": "status_equals", "expected": "success"},
    {"type": "node_executed", "node": "Normalize Holdings"},
    {"type": "node_error_absent", "node": "Normalize Holdings"},
    {"type": "node_item_count", "node": "Normalize Holdings", "output_index": 0, "expected": 5},
    {"type": "json_pointer_equals", "pointer": "/data/resultData/runData/Normalize Holdings/0/data/main/0/0/json/fund_id", "expected": "FND-001"}
  ]
}
```

Run:

```bash
python scripts/assert_execution.py \
  --execution <execution.json> \
  --assertions <assertions.json> \
  --out <assertion-result.json>
```

Read `references/assertion-contract.md` for supported assertion types.

Do not replace an exact assertion with “the output looks correct.” If the correct semantic property cannot be expressed yet, extend the assertion harness rather than weakening the oracle.

## 10. COMPARE — locate semantic differences

When a baseline execution exists:

```bash
python scripts/execution_diff.py \
  --baseline <baseline-execution.json> \
  --candidate <candidate-execution.json> \
  --workflow <workflow.json> \
  --out <diff.json>
```

The semantic diff removes a narrow set of volatile timing/execution metadata but preserves node outputs and errors. It reports changed nodes in workflow order when the workflow snapshot is supplied.

A difference is evidence, not automatically a regression. Interpret it against the test plan.

## 11. MATRIX — run regression fixtures serially

For a representative regression set, define a matrix and run:

```bash
python scripts/run_matrix.py \
  --config <lab-config.json> \
  --deployment <deployment.json> \
  --matrix <matrix.json> \
  --artifacts-dir <run-directory> \
  --out <matrix-summary.json>
```

The matrix runner enforces the configured case-count bound and executes cases serially by default. Each case gets its own invocation receipt, raw execution, assertion result, and summary.

Use `--continue-on-failure` only when collecting the remaining cases adds useful evidence and does not increase side-effect risk.

## 12. CLEANUP — remove ephemeral infrastructure

Unless explicitly retained for immediate inspection:

```bash
python scripts/cleanup_lab.py \
  --config <lab-config.json> \
  --deployment <deployment.json>
```

Cleanup must re-fetch the workflow and verify the expected `LAB__`-style prefix before deletion. It unpublishes first when possible, then deletes.

Never delete by an unverified workflow ID taken only from user prose or an untrusted artifact.

## 13. REPORT — return laboratory evidence

Return a compact result containing:

- test question;
- strategy and boundary;
- fixture provenance/digest;
- lab workflow ID/version;
- execution ID/status;
- assertion pass/fail counts;
- meaningful semantic differences;
- harness limitations or redaction gaps;
- cleanup state;
- artifact paths.

If the test was invoked from a debugging case, append the result to that case's experiment evidence. Do not make a new root-cause claim unless `debug-n8n-workflow` evaluates the evidence.

## Script routing

Use the scripts rather than reimplementing fragile mechanics ad hoc:

- `scripts/lab_preflight.py` — configuration and read-only connectivity gate.
- `scripts/n8n_api.py` — minimal public-API client and explicit read/snapshot operations.
- `scripts/validate_test_plan.py` — deterministic test-intent and strategy gate.
- `scripts/extract_fixture.py` — capture node-output items from historical execution JSON.
- `scripts/validate_fixture.py` — validate size/shape/provenance and detect binary portability issues.
- `scripts/make_replay_clone.py` — compile a downstream replay cone with a fixture boundary.
- `scripts/validate_lab_workflow.py` — side-effect and trigger safety gate.
- `scripts/deploy_lab_clone.py` — safely create/publish an ephemeral lab workflow.
- `scripts/trigger_webhook.py` — serial fixture invocation with execution-correlation receipt.
- `scripts/wait_execution.py` — find the unique new execution and capture detailed data.
- `scripts/retry_lab_execution.py` — safely retry only a validated current lab workflow and capture the retry execution.
- `scripts/assert_execution.py` — deterministic semantic assertions.
- `scripts/execution_diff.py` — baseline/candidate node-level semantic diff.
- `scripts/run_matrix.py` — bounded serial regression matrix.
- `scripts/cleanup_lab.py` — verified unpublish/delete cleanup.
- `scripts/selftest.py` — offline harness self-test; run before using a modified version of the skill.

## Reference routing

Read only what the current test needs:

- `references/lab-safety-model.md` — lab config, side-effect policies, environment guardrails.
- `references/test-plan-contract.md` — machine-readable experiment intent and strategy requirements.
- `references/execution-strategies.md` — choose replay, retry, native-trigger, or snapshot-only mode.
- `references/replay-boundary-rules.md` — semantic validity of boundary substitution.
- `references/fixture-contract.md` — portable fixture schema and provenance.
- `references/assertion-contract.md` — deterministic assertion types.
- `references/execution-data-anatomy.md` — n8n execution fields, redaction, and run data.
- `references/credential-remapping.md` — credential-reference rules across environments.
- `references/n8n-api-current.md` — API endpoints/scopes relied on by this harness.
- `references/cleanup-and-failure-policy.md` — rollback, ambiguity, timeout, and cleanup behavior.

## Harness integrity

Before first use after installing or modifying this skill, run:

```bash
python scripts/selftest.py
```

The self-test is offline and must not contact n8n. It validates fixture extraction, replay-cone compilation, cross-boundary reference detection, safety classification, assertion evaluation, and semantic diff behavior on synthetic examples.

## Seed assets

Prefer copying and editing these schemas rather than inventing new formats:

- `assets/lab-config.example.json`
- `assets/test-plan.example.json`
- `assets/fixture.example.json`
- `assets/side-effects.example.json`
- `assets/credential-map.example.json`
- `assets/assertions.example.json`
- `assets/matrix.example.json`
