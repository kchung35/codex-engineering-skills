# Requirements and invariants

A workflow requirement is useful when it is falsifiable.

Separate:
- required outcomes;
- prohibited outcomes;
- existing invariants;
- acceptance criteria;
- out-of-scope behavior;
- unknowns that could change the design.

## Invariant categories

Consider only those relevant to the workflow:
- schema/field compatibility;
- item cardinality/order;
- database keys and uniqueness;
- downstream workflow contracts;
- trigger behavior;
- external side effects;
- human-review gates;
- latency/cadence;
- retry/reprocessing behavior;
- provenance/confidence metadata.

## Compatibility

Do not infer that a field is disposable because no immediate consumer appears in the local graph. Check cross-workflow/database/API consumers when the field is part of a shared contract.

For additive schema changes, prefer backward-compatible additions unless the user explicitly wants a breaking change.

For removals/renames, identify every consumer or state the uncertainty.

## Acceptance criteria

Prefer:
- exact output shapes;
- counts/cardinality;
- database effects;
- idempotency outcomes;
- error-path outcomes;
- retry behavior;
- preserved invariants.

Avoid vague words such as robust, scalable, clean, correct, or production-ready without measurable meaning.
