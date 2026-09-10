# n8n-specific review lenses

Use these checks only where the diff/risk scan makes them relevant.

## Data and item semantics

Check whether the change alters:

- zero/one/many item behavior;
- item ordering;
- aggregation or fan-out;
- paired-item lineage;
- `$json`, `$input`, `$('Node')`, or other cross-node expression assumptions;
- branches whose referenced node may not have executed;
- Merge/Loop/Split/Switch semantics.

Programmatic nodes can require explicit item-linking metadata when outputs must map back to inputs. Missing lineage can break downstream item references.

## Error semantics

Inspect changes to:

- `onError` / legacy continue-on-fail behavior;
- `retryOnFail`, retry count, retry delay;
- error workflow settings;
- explicit Stop And Error nodes;
- downstream contracts after a tolerated failure.

A workflow that "continues" after failure needs a defined failure representation; otherwise downstream success can mask an incomplete operation.

## Trigger and publication semantics

Review webhook/schedule/poll/trigger changes as externally visible API behavior. Check path/auth/event scope and duplicate-delivery assumptions.

Keep review read-only. Do not update a published workflow from this skill. Current n8n update APIs may republish an active workflow unless draft-preserving behavior is explicitly requested by the caller.

## Workflow settings

Treat changes to timezone, execution order, caller policy, allowed callers, redaction policy, error workflow, or MCP availability as potentially behavioral/security relevant.

## Node type versions

A `typeVersion` change can alter behavior even when visible parameters are unchanged. Require compatibility review and runtime coverage for the affected path.
