# Live n8n Test Protocol

## Principle

A test environment should preserve the semantics that matter to the bug while preventing unintended production side effects.

## Preferred environment order

1. Dedicated development/test n8n instance matching production closely.
2. Isolated workflow/project on a non-production instance.
3. Safely cloned workflow with controlled entry point and side-effect isolation.
4. Production replay only when explicitly authorized and demonstrably safe.

If the organization uses n8n source-control environments, respect its established development-to-production direction rather than creating an ad-hoc reverse synchronization path.

Current environment docs: https://docs.n8n.io/source-control-environments/create-environments/

## Before execution

Capture:

- source workflow/execution ID;
- workflow snapshot/version;
- test workflow ID;
- n8n/runtime/node versions where relevant;
- fixture provenance;
- credential references used;
- every external side effect that could occur.

## Side-effect isolation

For nodes that send, write, delete, trade, publish, message, mutate databases, or otherwise create external effects, choose one:

- use a dedicated sandbox/test credential;
- redirect to a test endpoint/schema/table/mailbox;
- replace with a deterministic stub when the external side effect is not under test;
- disable the side-effecting branch while asserting the payload immediately before it.

Do not silently stub a dependency if the suspected cause depends on that dependency's real behavior.

## Fixture sources

Prefer, in order:

1. exact historical failing execution input;
2. minimized fixture derived from it;
3. nearest known-good historical input;
4. synthetic boundary cases.

n8n supports loading data from previous executions into the workflow UI and retrying failed workflows using previous execution data. Use these facilities when they answer the diagnostic question safely.

Current execution docs: https://docs.n8n.io/workflows/executions/all-executions/

## Assertions

Assert semantics at the relevant boundary:

- item count;
- IDs/keys preserved;
- canonical values;
- branch taken;
- database state;
- external payload;
- idempotency outcome;
- error classification;
- retry behavior.

Do not snapshot enormous payloads when a small set of semantic invariants proves correctness.

## Verification matrix

Mandatory when applicable:

- original failing fixture;
- one historical known-good fixture;
- nearest boundary/negative case.

Conditional:

- 0/1/many items;
- missing/null/empty;
- duplicate/retry;
- concurrency/order;
- timeout/rate limit;
- API schema variation;
- large payload;
- alternate branch;
- partial dependency failure.

## Failure handling

If a live test fails:

1. preserve the execution;
2. identify the earliest semantic divergence;
3. compare it to the predicted outcome;
4. update the hypothesis/model;
5. return to investigation rather than layering a second speculative fix.
