---
name: build-n8n-workflow
description: "Design and implement new n8n workflows or intentional changes to existing workflows with explicit requirements, data contracts, failure semantics, state/idempotency, side-effect boundaries, observability, minimal blast radius, and static validation. Use when the user asks to build, add, refactor, restructure, migrate, or intentionally modify n8n workflow behavior. Do not use to diagnose unexplained failures, run live regression experiments, or deploy/publish changes to production."
---

# Build n8n Workflow

Design and construct n8n workflow candidates as engineering systems, not as collections of nodes.

This skill owns **intentional design and implementation**. It does not own forensic root-cause diagnosis, live-lab execution, or production release.

Use the lifecycle:

`SCOPE -> CONTEXT -> REQUIREMENTS -> BOUNDARIES -> OPTIONS -> DECISION -> CONTRACTS -> FAILURE/STATE -> PLAN -> BUILD -> STATIC_VALIDATE -> HANDOFF`

Scale the ceremony to the change. A two-node deterministic change does not need an architecture essay; a stateful multi-system workflow does.

## Non-negotiable rules

1. Preserve the user's requested behavior and scope. Do not broaden a change because a redesign looks cleaner.
2. Never use this skill to patch an unexplained symptom. If the current behavior is not understood, hand the problem to `debug-n8n-workflow` before changing architecture.
3. Define acceptance criteria before implementation for any non-trivial change.
4. Treat data shape, side effects, state, retries, and failure behavior as part of the design, not cleanup after coding.
5. Prefer the smallest coherent change that satisfies requirements and invariants.
6. Separate pure transformation from I/O when practical. Side-effect boundaries must be explicit.
7. External writes require an idempotency/retry decision. "We probably won't retry" is not a design.
8. Do not rely on hidden cross-node state when an explicit data contract can carry the value.
9. Preserve n8n item lineage/cardinality semantics. Do not casually replace itemwise flow with one aggregate object or vice versa.
10. Use sub-workflows for stable reusable boundaries, isolation, or meaningful ownership—not merely to make the canvas look smaller.
11. Prefer native nodes and simple expressions for ordinary transformations. Use Code nodes when they materially improve correctness, clarity, or capability.
12. Keep Code nodes narrow: explicit input assumptions, explicit output shape, deterministic behavior where feasible, and preserved item linkage when outputs map to inputs.
13. Every branch, loop, merge, wait, retry, and continuation path needs an explicit semantic reason.
14. Error swallowing is prohibited by default. If execution continues after an error, define exactly what downstream contract represents the failure.
15. Production publication is out of scope. Candidate updates to a currently published workflow must use draft-preserving semantics (`publishIfActive=false`) when a live API is used outside the release skill.
16. Never place plaintext credentials or secret values in workflow JSON, build artifacts, logs, or source control.
17. Build artifacts and static checks are evidence of structural quality, not proof of runtime correctness. Hand non-trivial candidates to `test-n8n-workflow`.
18. If static validation reveals an unexplained existing defect, stop changing the design and return evidence to `debug-n8n-workflow`.

## 1. SCOPE — classify the change before designing

Classify the request using the **highest** applicable level:

- `LOCAL`: bounded change to one small region; no new external side effect, persistent state, trigger semantics, or shared contract.
- `FLOW`: branching, merging, looping, item cardinality, multiple connected regions, or meaningful control-flow change.
- `INTEGRATION`: new/changed external API, credentialed system, database interaction, file transfer, queue, or external write.
- `STATEFUL`: deduplication, retries, concurrency, checkpoints, waits, persistent state, reprocessing, or exactly/at-least-once concerns.
- `ARCHITECTURAL`: cross-workflow contract, reusable sub-workflow, shared component, major restructuring, migration, or multiple systems/owners.

Record the classification in `build.json`.

Read [references/change-depth.md](references/change-depth.md) for the artifact depth required at each class.

Do not artificially downgrade a change to avoid design work.

## 2. CONTEXT — reconstruct only what can constrain the design

Before proposing a solution, inspect the relevant current workflow/repository/project information.

For an existing workflow, capture or load the exact current workflow JSON and run:

```bash
python scripts/analyze_workflow.py <workflow.json> --out <analysis.json>
python scripts/workflow_graph.py <workflow.json> --out <graph.json>
```

Understand at minimum:

- relevant trigger and entry contract;
- affected nodes and downstream consumers;
- item/cardinality behavior;
- expressions that reach across node boundaries;
- credentials and external systems referenced;
- database/state interactions;
- sub-workflows;
- workflow settings relevant to execution/error behavior;
- current side-effect boundaries.

Do not read unrelated project documentation merely because it exists.

When modifying an existing workflow, distinguish:
- behavior that **must remain invariant**;
- behavior explicitly requested to change;
- behavior that is incidental and must not be silently redesigned.

## 3. REQUIREMENTS — convert the request into falsifiable behavior

For `FLOW` and above, write `requirements.json` before implementation.

Start from `assets/requirements.example.json`.

Separate:

- `must_do`: required behavior;
- `must_not_do`: prohibited behavior;
- `invariants`: existing behavior/contracts that must remain true;
- `acceptance`: observable pass conditions;
- `out_of_scope`: explicit exclusions;
- `unknowns`: facts that materially affect design and are not yet established.

An acceptance criterion should be externally observable or mechanically testable.

Bad:
> "The workflow should be robust."

Better:
> "Reprocessing the same `DocumentID` does not create a second database row and produces the same canonical payload."

Run:

```bash
python scripts/validate_requirements.py <requirements.json>
```

Read [references/requirements-and-invariants.md](references/requirements-and-invariants.md) when requirements are ambiguous or involve compatibility.

## 4. BOUNDARIES — decide where correctness lives

Before drawing nodes, define the semantic boundaries of the system.

Identify:

- entry boundary;
- canonicalization/normalization boundary;
- pure transformation regions;
- side-effect boundaries;
- persistence/state boundary;
- external integration boundaries;
- human-review boundary if any;
- exit/output boundary;
- reusable sub-workflow boundaries if justified.

For each important boundary, answer:

1. What enters?
2. What leaves?
3. What invariants hold?
4. Can it be retried safely?
5. What observable evidence proves success/failure?

For complicated workflows, create `contracts.json` from `assets/contracts.example.json`.

Read [references/data-contracts.md](references/data-contracts.md).

## 5. OPTIONS — explore architecture before committing

For `ARCHITECTURAL` changes, and for lower-risk changes where materially different designs exist, generate 2–4 credible options.

Do not create fake alternatives that differ only in naming.

Evaluate each against:

- correctness;
- compatibility;
- blast radius;
- operational complexity;
- testability;
- observability;
- failure isolation;
- idempotency/retry behavior;
- maintainability/agent legibility;
- implementation cost.

Use `assets/design-decision.example.json` for a persistent decision record.

Prefer a simpler design when it satisfies the same invariants with fewer hidden dependencies.

Do not optimize for minimum node count. Optimize for understandable semantics and minimum accidental coupling.

Read [references/architecture-principles.md](references/architecture-principles.md).

## 6. DECISION — choose a design and freeze the invariants

The decision record must state:

- selected option;
- why it wins;
- important rejected alternatives;
- assumptions on which the choice depends;
- expected blast radius;
- intentional behavior changes;
- behavior guaranteed unchanged;
- rollback/migration implications.

After this point, implementation should realize the chosen design, not continuously reinvent it.

If new information invalidates the decision, return to the earliest affected stage and update the record.

## 7. CONTRACTS — design data before expressions

For every important cross-node or cross-workflow interface, define:

- field names and types;
- required vs optional;
- null semantics;
- array/item cardinality;
- identifiers and uniqueness;
- timestamps/timezones;
- canonical labels/enums;
- provenance/confidence metadata where relevant;
- failure representation;
- version/compatibility expectations where the contract is shared.

Normalize ambiguous external data near the ingestion boundary instead of forcing downstream nodes to understand many source variants.

Prefer carrying required values in the current item over long-range node references. Long-range references are not forbidden, but each should have a clear reason.

If a Code node creates multiple outputs or changes item cardinality, explicitly preserve/define item linkage semantics.

Read:
- [references/data-contracts.md](references/data-contracts.md)
- [references/flow-control-and-items.md](references/flow-control-and-items.md) when item cardinality, Merge, loops, or cross-node references matter.

## 8. FAILURE/STATE — design the unhappy path before building it

For `INTEGRATION`, `STATEFUL`, and `ARCHITECTURAL` changes, explicitly model:

### Failure
- transient vs permanent failures;
- retry ownership;
- retry count/backoff where relevant;
- timeout behavior;
- partial success;
- continuation vs stop;
- error workflow/escalation;
- poison/bad input handling.

### State
- idempotency key;
- deduplication boundary;
- transaction/atomicity boundary;
- reprocessing behavior;
- concurrent execution behavior;
- checkpoint/resume semantics;
- ordering assumptions;
- stale-state behavior.

### Side effects
Classify every external interaction:
- `READ`
- `CREATE`
- `UPDATE`
- `DELETE`
- `SEND/PUBLISH`
- `EXECUTE`
- `UNKNOWN`

Unknown side effects block design closure until resolved.

For any non-read operation, answer:

> What happens if n8n executes this node twice?

Read:
- [references/state-and-idempotency.md](references/state-and-idempotency.md)
- [references/failure-and-recovery.md](references/failure-and-recovery.md)
- [references/integrations-and-side-effects.md](references/integrations-and-side-effects.md)

Use `assets/side-effects.example.json` and `assets/failure-policy.example.json` where applicable.

## 9. OBSERVABILITY — make future debugging cheap

For `FLOW` and above, define the identifiers and evidence needed to reconstruct a run.

Prefer stable business/correlation identifiers over prose logs.

Consider:
- workflow execution ID;
- business object ID / document ID / package ID;
- upstream source ID;
- idempotency key;
- canonicalization version;
- stage/status;
- external request/reference ID;
- timestamps and durations;
- structured error category;
- retry attempt;
- selected decision path where useful.

Do not log credentials or unnecessarily sensitive payloads.

Use n8n execution custom data/structured persistence where available and appropriate; do not invent a new logging database for a simple workflow without need.

Read [references/observability.md](references/observability.md).

## 10. PLAN — map design into concrete node-level changes

Before implementation, produce `implementation-plan.json` for `FLOW` and above.

Every operation should specify:

- action: add/update/remove/rewire/extract-subworkflow;
- target node or boundary;
- reason;
- contract change;
- side-effect change;
- downstream dependencies affected;
- test obligation.

Order the plan so contract-producing changes precede consumers when practical.

For existing workflows, generate an impact baseline:

```bash
python scripts/analyze_workflow.py <source.json> --out <before-analysis.json>
```

## 11. BUILD — construct the candidate, not production

Build a candidate workflow JSON or modify the approved non-production artifact.

When using the n8n public API for an existing published workflow, save as a draft by setting `publishIfActive=false`. The current API otherwise republishes an updated published workflow by default.

Use:
```bash
python scripts/sanitize_candidate.py <candidate.json> \
  --mode <create|update> \
  --out <api-payload.json>
```

The sanitizer removes known read-only response fields and emits only create/update-compatible workflow fields.

### Implementation preferences

Prefer:
- explicit node names that describe semantic responsibility;
- one clear responsibility per node/region;
- deterministic nodes/expressions for simple transformations;
- Code nodes for logic that becomes less correct or less readable when stretched across many expression nodes;
- early normalization of unstable external schemas;
- explicit branches for materially different failure/business outcomes;
- bounded loops and pagination;
- sub-workflows for stable reusable contracts, isolation, or ownership boundaries;
- comments/node notes for non-obvious invariants, not narration of obvious nodes.

Avoid:
- giant Code nodes containing an entire workflow;
- dozens of tiny nodes that obscure one atomic transformation;
- duplicated business logic across branches;
- hidden reliance on pinned data;
- `continueOnFail`-style behavior without an explicit downstream error contract;
- implicit state in workflow static data when durable persistence is required;
- unrelated refactors inside a requested feature.

Read [references/implementation-patterns.md](references/implementation-patterns.md).

## 12. STATIC_VALIDATE — mechanically reject structural mistakes

Run:

```bash
python scripts/validate_design_artifacts.py <build-dir> --report <design-validation.json>
python scripts/validate_workflow.py <candidate.json> --report <validation.json>
python scripts/audit_expressions.py <candidate.json> --report <expression-audit.json>
```

For modifications:

```bash
python scripts/change_impact.py \
  --before <source.json> \
  --after <candidate.json> \
  --out <impact.json>
```

The structural validator checks, among other things:

- required top-level workflow shape;
- unique node IDs and names;
- connection sources/targets;
- impossible dangling connections;
- node positions/types/type versions;
- deprecated `continueOnFail` use;
- error-policy contradictions;
- duplicate webhook IDs;
- caller-policy coherence;
- suspicious trigger count/shape;
- Code-node output-risk patterns;
- expressions referencing missing nodes;
- workflow settings changes with operational consequences.

Warnings require review; errors block handoff.

Static validation is not runtime verification.

## 13. HANDOFF — prove the candidate in n8n

For non-trivial changes, hand the candidate plus requirements and test obligations to `test-n8n-workflow` when that skill is available.

The handoff should include:

- source workflow/version if modifying;
- candidate workflow;
- requirements/acceptance criteria;
- contracts;
- side-effect manifest;
- failure/state policy;
- implementation plan;
- static validation report;
- change-impact report;
- required fixtures and boundary conditions.

For a `LOCAL` change with no runtime-sensitive behavior, focused local/static validation may be sufficient if the user did not request live verification. Do not claim hosted n8n behavior was tested when it was not.

If testing exposes unexplained behavior, hand the execution evidence to `debug-n8n-workflow`.

Production publication belongs to `release-n8n-change`, not this skill.

## Build state

For non-trivial work, keep persistent state under:

```text
.agent-builds/
  BUILD-<id>/
    build.json
    requirements.json
    context.json
    contracts.json
    design-options.json
    decision.json
    side-effects.json
    failure-policy.json
    observability.json
    implementation-plan.json
    source-workflow.json
    candidate-workflow.json
    validation.json
    expression-audit.json
    impact.json
    handoff.json
    artifacts/
```

Use:

```bash
python scripts/init_build.py --title "<short title>" --class FLOW --mode <NEW|MODIFY>
python scripts/build_gate.py <build-dir> --to BUILD
python scripts/build_summary.py <build-dir>
```

The gate is a procedural floor, not proof that the design is correct.

## Completion standard

Do not call a build complete merely because valid JSON was produced.

A non-trivial build is ready for testing when:

- requirements and acceptance criteria are explicit;
- current invariants are identified;
- design choice is justified at the appropriate depth;
- important data contracts are explicit;
- side effects and state/retry semantics are resolved;
- candidate scope matches the decision;
- static validation has no blocking errors;
- impact is understood;
- test obligations are specified.

A build becomes verified only after the required runtime tests pass.
