# Fix Selection

## Objective

Choose the smallest change that robustly resolves the confirmed causal set while preserving required behavior.

"Smallest" means smallest semantic/blast-radius change, not necessarily fewest lines.

## Candidate comparison

For each credible option evaluate:

- causes addressed;
- invariants preserved;
- nodes/files/contracts touched;
- behavior changed;
- downstream/upstream compatibility;
- data migration/backfill;
- new state or operational burden;
- new failure modes;
- observability;
- reversibility;
- testability;
- future maintenance complexity.

## Preferred hierarchy

1. Correct the broken local contract/logic if architecture is sound.
2. Add validation/guarding where malformed input is a legitimate boundary condition.
3. Move responsibility to a clearer boundary if the current location makes correctness fragile.
4. Change architecture only when architecture is causal, repeatedly generates the defect class, or a local patch would be brittle/unsafe.

## Reject fixes that

- mask the symptom without correcting its generating mechanism;
- silently drop malformed data when correctness requires surfacing it;
- turn a deterministic failure into an unnoticed wrong result;
- add retries to a non-idempotent operation without idempotency controls;
- broaden permissions or expose secrets for convenience;
- create duplicate sources of truth;
- depend on undocumented item ordering/cardinality assumptions;
- couple unrelated branches/components;
- require large rewrites with no causal justification.

## Acceptance tests first

Before implementation, write the observations that must become true if the fix is correct and the behavior that must remain unchanged. These become verification assertions.
