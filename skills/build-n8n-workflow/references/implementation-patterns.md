# Implementation patterns

These are preferences, not absolute rules.

## Native node vs Code node

Prefer native nodes/expressions when the operation is simple and semantically obvious.

Prefer a Code node when:
- the logic is easier to validate as one deterministic function;
- many expression nodes would duplicate logic;
- complex normalization needs explicit tests;
- algorithmic transformation is clearer in code.

Avoid making Code nodes mini-applications that hide I/O, state, branching, and many responsibilities.

## Normalization stage

A strong pattern is:
`TRIGGER/READ -> VALIDATE -> NORMALIZE -> DECIDE/TRANSFORM -> SIDE EFFECT -> RECORD RESULT`

Not every workflow needs every stage.

## Explicit status envelope

For pipelines, a status envelope can reduce ambiguity:
- `status`;
- `stage`;
- `entity_id`;
- `payload`;
- `errors`;
- `meta`.

Use only when it clarifies multi-stage processing; do not wrap simple flows unnecessarily.

## Side-effect boundary

Keep the data needed for a write together immediately before the write. Validate identifiers and required fields before crossing the boundary.

## Error branches

Use explicit branches when a failure is a business outcome (e.g. "needs review") rather than an infrastructure crash.

## Node names

Name nodes by responsibility/outcome, not implementation trivia:
- `Normalize Holdings`
- `Upsert Fund Snapshot`
- `Route Low Confidence`
rather than
- `Code 7`
- `HTTP Request 3`.

## Notes

Use node notes for non-obvious invariants, external assumptions, and why a strange workaround exists. Do not narrate obvious settings.
