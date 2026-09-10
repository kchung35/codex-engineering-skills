# Execution strategies

Choose the strategy that preserves the semantic property under test with the smallest blast radius.

## BOUNDARY_REPLAY

Default for downstream workflow logic.

Mechanism:

1. capture the output items of a stable boundary node;
2. compile the downstream reachable cone from the selected output index;
3. replace the boundary node with a Code-node fixture injector using the same name and ID;
4. add an ephemeral Webhook trigger;
5. publish only on the non-production lab instance;
6. POST the fixture and retrieve the resulting execution.

Strengths:

- exact control over input shape;
- avoids real upstream triggers;
- isolates the relevant causal cone;
- deterministic and cheap to repeat;
- can reuse historical failing and known-good node outputs.

Invalid when:

- the bug is in the bypassed boundary node or upstream trigger;
- retained downstream expressions reference removed upstream nodes;
- execution depends on upstream static state, binary storage, paired-item lineage, or cross-workflow context not preserved by the fixture;
- the chosen boundary has multiple semantically meaningful output branches and only one output is being replayed;
- timing/concurrency between upstream branches is causal.

## RETRY_IN_LAB

Use only for executions already created in the configured non-production lab.

The n8n API itself can retry using either the workflow stored with the original execution or the currently saved workflow. This harness intentionally narrows that freedom: `retry_lab_execution.py` only retries a workflow carrying the configured lab prefix, validates the current workflow against the side-effect manifest, and uses `loadWorkflow=true`.

This is useful for A/B testing a saved lab change against identical retry input without exposing an arbitrary historical-workflow execution path. Do not use when the execution can repeat external side effects that have not been isolated. A retry is a real execution, not a dry run.

## NATIVE_TRIGGER_LAB

Use when the trigger/integration itself is under test.

Examples:

- webhook authentication/header parsing;
- polling semantics;
- scheduler/timezone behavior;
- email/queue trigger behavior;
- OAuth/credential behavior;
- upstream API pagination or rate-limiting;
- binary upload/download behavior.

Requirements:

- dedicated lab account/system or explicitly isolated test target;
- test credential references already provisioned;
- a deterministic event generator where possible;
- assertions that distinguish trigger correctness from downstream correctness.

## SNAPSHOT_ONLY

Read-only mode. Capture workflow/execution data and compare without running anything.

Use when live execution is not authorized or when existing evidence is already sufficient.

## Selection rule

Ask: "What is the earliest boundary that can be controlled without removing the mechanism being tested?"

Choose the earliest *safe and semantically faithful* boundary, not simply the earliest node in the workflow.
