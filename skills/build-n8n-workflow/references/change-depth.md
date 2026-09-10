# Change depth

Use the highest applicable change class. The class determines the minimum evidence, not the amount of prose.

## LOCAL

Use for a bounded change with no new external side effect, persistent state, trigger semantics, or shared contract.

Minimum:
- concise requested behavior;
- affected region;
- invariants that matter;
- candidate;
- structural/expression validation;
- focused test obligation.

## FLOW

Use when branching, merging, loops, cardinality, or several connected regions change.

Add:
- requirements.json;
- explicit acceptance criteria;
- item/cardinality model;
- implementation plan;
- observability decision;
- before/after impact.

## INTEGRATION

Use when a database/API/credentialed system or external write changes.

Add:
- external contract;
- side-effect manifest;
- timeout/retry semantics;
- idempotency decision for writes;
- credential reference plan;
- negative/error cases.

## STATEFUL

Use when correctness depends on deduplication, reprocessing, concurrency, waits, checkpoints, ordering, or persistent state.

Add:
- state machine or state table;
- idempotency key;
- concurrency assumptions;
- atomicity/transaction boundary;
- duplicate/retry cases;
- recovery semantics.

## ARCHITECTURAL

Use for sub-workflow extraction, shared contracts, major restructuring, migration, or multiple systems/owners.

Add:
- 2–4 real design options;
- decision record;
- compatibility/migration plan;
- rollback implications;
- ownership/boundary rationale;
- full test handoff.

Do not promote simple changes into architecture projects. Do not demote high-risk changes because the visible node edit is small.
