# Requirement and invariant coverage

## Acceptance criteria

Every explicit acceptance criterion must receive one status:

- `VERIFIED`
- `CONTRADICTED`
- `NOT_VERIFIED`
- `NOT_APPLICABLE`

`NOT_APPLICABLE` requires a concrete reason; it must not be used to avoid difficult testing.

When the workflow behavior changed, a `VERIFIED` acceptance criterion must cite at least one bound passing runtime test whose evidence manifest explicitly declares support for that criterion. Static evidence is appropriate for properties that are genuinely static, such as "no new credential reference is introduced".

## Invariants

Invariants are behaviors or contracts that must remain true despite the change. Examples include:

- stable identifiers;
- existing valid input handling;
- item cardinality/ordering guarantees;
- destination uniqueness;
- no new external writes;
- sub-workflow interface compatibility.

Do not assume an invariant is preserved because the owning node is unchanged. A changed upstream value, branch, item count, execution order, or retry behavior can violate downstream invariants.

## Coverage evidence IDs

Runtime evidence IDs must resolve to usable entries emitted by `bind_test_evidence.py`.

Findings can support `CONTRADICTED` statuses. Static deterministic artifacts may be cited with descriptive identifiers, but do not use a model-authored statement as the sole evidence for a behavioral `VERIFIED` status.

## Test adequacy

Coverage is not merely "one test per requirement." The test must exercise the causal path that would falsify the criterion.
