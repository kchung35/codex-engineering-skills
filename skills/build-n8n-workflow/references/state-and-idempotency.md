# State and idempotency

Every external mutation needs duplicate semantics.

Ask:
> What happens if this node runs twice with the same logical business event?

## Idempotency keys

A good idempotency key is:
- stable across retries of the same logical event;
- different across distinct logical events;
- available before the side effect;
- persisted/checked atomically enough for the failure model.

Examples can include document ID + processing version, provider event ID, or business object ID + operation type.

## State locations

Prefer durable systems for durable state:
- database table/constraint;
- provider idempotency key;
- queue/message key;
- dedicated state store.

Workflow static data is not a substitute for durable transactional state when correctness depends on it.

## Concurrency

Define whether concurrent executions can touch the same logical entity.

If yes, decide whether correctness requires:
- uniqueness constraint;
- compare-and-swap/version column;
- row lock/transaction;
- serialization;
- conflict retry;
- last-write-wins (only if semantically valid).

## Partial success

For multiple side effects, decide:
- whether they form one logical transaction;
- whether compensation is possible;
- whether a checkpoint records completed effects;
- what replay does after a partial failure.

## Ordering

Do not assume chronological execution order unless the trigger/queue/runtime guarantees it. If ordering matters, persist sequence/version information and enforce it.

## Reprocessing

Specify whether reprocessing:
- is a no-op;
- recalculates and overwrites;
- creates a new version;
- repairs missing downstream effects.

"Retry" and "reprocess" are not necessarily the same operation.
