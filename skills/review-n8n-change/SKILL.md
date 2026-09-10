---
name: review-n8n-change
description: "Independently review an n8n workflow change, refactor, migration, or bug-fix candidate against stated requirements, prior behavior, workflow semantics, data contracts, failure/idempotency rules, side effects, security, regression risk, and bound runtime evidence. Use when asked to review, audit, approve, challenge, validate, or sign off an n8n change before release. Do not use to design or implement the change, diagnose an unexplained incident from scratch, execute production mutations, or publish/release workflows."
---

# Review n8n Change

Review an n8n change as an independent verifier, not as a second implementation pass.

This skill owns **adversarial review and release-readiness judgment**. It does not own design, implementation, forensic debugging, live-lab mechanics, or production release.

Use the lifecycle:

`INTAKE -> BIND -> RECONSTRUCT -> DIFF -> REVIEW -> ATTACK -> COVERAGE -> VERDICT -> HANDOFF`

The core objective is not to find many comments. It is to determine whether the exact candidate is supported by enough evidence to satisfy the intended behavior without introducing material regressions.

## Non-negotiable rules

1. Review the actual candidate, not the author's description of the candidate.
2. Reconstruct intent from requirements, invariants, source behavior, and observable artifacts before relying on author rationale.
3. Treat author rationale as a hypothesis to verify, never as evidence by itself.
4. Remain read-only with respect to the workflow being reviewed. Do not modify, publish, activate, retry, delete, or deploy the candidate from this skill.
5. Do not convert review findings into opportunistic refactors. Separate defects from preferences.
6. Bind runtime evidence to the exact candidate snapshot. Evidence produced against another behavioral fingerprint is stale for release-readiness purposes.
7. A passing test suite is evidence, not proof of completeness. Review whether the tests cover the changed contracts and material failure modes.
8. Absence of discovered defects is not sufficient for `PASS`. Requirement/invariant coverage and mandatory review lenses must also be complete.
9. Do not manufacture findings to appear thorough. Every defect claim must identify evidence and a credible failure mechanism.
10. Record uncertain but material concerns as `NEEDS_EVIDENCE`, not as confirmed defects.
11. Distinguish pre-existing defects from regressions introduced by the candidate. Do not reject the candidate for unrelated legacy problems unless the candidate materially worsens or depends on them.
12. Apply review depth proportional to change class and actual risk signals. Do not spend equal effort on every node.
13. Any behavioral workflow change normally requires runtime evidence before release-readiness `PASS`.
14. Redacted, truncated, ambiguous, stale, or unbound execution data cannot satisfy a runtime evidence obligation.
15. Any changed external write, persistent state, retry path, or duplicate-sensitive action requires explicit state/idempotency review.
16. Any changed credential reference, webhook/trigger, external integration, Code node, caller policy, MCP exposure, or security-relevant setting requires the corresponding review lens.
17. High-severity unresolved defects block approval. High-severity evidence gaps block a confident verdict.
18. If review exposes a new unexplained failure mechanism, hand the evidence to `debug-n8n-workflow` rather than inventing a fix here.
19. If the design is wrong or incomplete, hand the finding to `build-n8n-workflow` rather than editing the candidate here.
20. If additional runtime evidence is required and non-production testing is authorized, hand a precise test obligation to `test-n8n-workflow`.

## 1. INTAKE — assemble the review packet

Start from `assets/review-packet.example.json` and create a review directory separate from the build/debug artifacts.

For a non-trivial review, initialize with:

```bash
python scripts/init_review.py \
  --title "<review title>" \
  --mode MODIFY \
  --change-class FLOW \
  --source <source-workflow.json> \
  --candidate <candidate-workflow.json> \
  --requirements <requirements.json> \
  --out-dir <review-dir>
```

The packet should point to, when available:

- source workflow snapshot;
- candidate workflow snapshot;
- requirements/invariants;
- build decision/contracts/failure/side-effect artifacts;
- debugger causal set for bug fixes;
- test plan(s) and result summary(s);
- optional author rationale, stored separately.

For `NEW` workflows, source may be null. For `MODIFY`, `REFACTOR`, `MIGRATION`, and `BUG_FIX`, source is required.

Validate the packet:

```bash
python scripts/validate_review_packet.py <review-dir>/review.json
```

Do not start substantive review if the candidate file cannot be resolved.

## 2. BIND — establish exact artifact identity

Before reading conclusions, fingerprint the source and candidate:

```bash
python scripts/fingerprint_workflow.py <candidate.json> --out <review-dir>/candidate-fingerprint.json
```

For an existing workflow, also fingerprint the source.

The fingerprint has two purposes:

- `behavior_sha256`: binds evidence to workflow behavior while ignoring purely visual/editor metadata;
- `artifact_sha256`: identifies the exact serialized review artifact after removing volatile server metadata.

When runtime test artifacts exist, create `test-evidence.json` from the seed and bind them:

```bash
python scripts/bind_test_evidence.py \
  --candidate <candidate.json> \
  --manifest <review-dir>/test-evidence.json \
  --out <review-dir>/bound-test-evidence.json
```

A test is release-relevant only when the test plan's source workflow snapshot has the same `behavior_sha256` as the reviewed candidate and the test result is interpretable.

Do not substitute timestamps, workflow names, or “this was tested after the change” for cryptographic binding.

Read [references/evidence-and-binding.md](references/evidence-and-binding.md) when runtime evidence is present or its provenance is unclear.

## 3. RECONSTRUCT — recover intent independently

Review in this evidence order:

1. user/stated requirements and acceptance criteria;
2. invariants and out-of-scope behavior;
3. source workflow behavior relevant to the change;
4. actual candidate workflow and structural diff;
5. deterministic/static analysis outputs;
6. runtime test evidence;
7. only then, author rationale/design decision/root-cause explanation.

If the author rationale has already appeared in the conversation, do not pretend it is unseen. Instead deliberately reconstruct the requirement and failure surface from independent artifacts before evaluating that rationale.

For each requirement, determine:

- what observable behavior would satisfy it;
- what would falsify it;
- which workflow boundary owns that behavior;
- what evidence would be strong enough to verify it.

Do not silently strengthen the user's requirement into a preferred architecture.

Read [references/review-method.md](references/review-method.md) and [references/requirement-and-invariant-coverage.md](references/requirement-and-invariant-coverage.md).

## 4. DIFF — review the change that actually exists

Generate a semantic workflow diff:

```bash
python scripts/workflow_diff.py \
  --source <source-workflow.json> \
  --candidate <candidate-workflow.json> \
  --out <review-dir>/workflow-diff.json
```

For a new workflow, omit `--source`.

Then generate deterministic risk signals:

```bash
python scripts/risk_scan.py \
  --candidate <candidate-workflow.json> \
  --diff <review-dir>/workflow-diff.json \
  --out <review-dir>/risk-scan.json
```

Use these outputs to focus review. They are **routing signals**, not defect findings.

At minimum, establish:

- nodes added/removed/behaviorally modified;
- connections/control flow changed;
- workflow settings changed;
- credential references changed;
- retry/error semantics changed;
- triggers/webhooks changed;
- Code nodes changed;
- state/static data changed;
- side-effecting or external I/O surfaces changed;
- node type-version changes;
- relevant visual-only changes that do not affect runtime semantics.

Do not review the entire workflow at equal depth when only a bounded region changed. Review the changed region plus the minimum transitive context required to assess its contracts and consequences.

## 5. REVIEW — apply mandatory lenses

Create `coverage.json` from `assets/coverage.example.json`.

The risk scanner emits `required_lenses`. Every required lens must end as `REVIEWED` or a justified `NOT_APPLICABLE`; otherwise the final gate cannot return `PASS`.

### Always consider

- `requirements`: does the candidate satisfy the stated behavior?
- `scope-diff`: is every material change intentional, and is requested scope preserved?
- `data-flow`: are inputs, outputs, field semantics, nullability, cardinality, and lineage coherent?
- `n8n-semantics`: are expressions, branches, merges, loops, item linking, and execution semantics correct where changed?
- `regression`: which previously valid paths or invariants can the change break?
- `test-adequacy`: do the tests actually exercise the changed behavior and likely failure surface?

### Conditionally required from risk signals

- `state-idempotency`: persistent writes, retries, deduplication, waits, concurrency, static state, reprocessing;
- `integration`: API/database/filesystem/external-service/credential behavior;
- `security`: credential changes, webhooks, Code nodes, risky node types, caller policies, MCP exposure, externally supplied URLs/queries;
- `failure-recovery`: retry/error-routing/continue behavior, partial failure, timeout paths;
- `compatibility`: type-version, shared contract, sub-workflow, caller, timezone, or execution-order changes;
- `observability`: changed side effects or failure handling without sufficient success/failure evidence;
- `performance`: loops, fan-out, large cardinality, repeated remote calls, expensive code, concurrency-sensitive design.

Read only the relevant references:

- [references/n8n-review-lenses.md](references/n8n-review-lenses.md)
- [references/state-idempotency-review.md](references/state-idempotency-review.md)
- [references/integration-security-review.md](references/integration-security-review.md)
- [references/performance-observability-review.md](references/performance-observability-review.md)

## 6. ATTACK — try to falsify the candidate

The adversarial pass should target credible failure scenarios, not enumerate arbitrary edge cases.

For each changed contract, high-risk signal, or important invariant, ask:

- What assumption must be true for this change to work?
- What is the nearest realistic counterexample?
- What input shape causes a different branch/cardinality than the happy path?
- What happens on zero items, one item, many items, missing fields, and nulls when relevant?
- What happens if an external dependency times out, returns a malformed response, or partially succeeds?
- What happens if the same logical event is replayed or execution retries after a side effect?
- What happens with concurrent executions if state is shared?
- What happens when a Merge/Loop/Switch path receives an unexpected branch count?
- What happens if node item lineage changes?
- What happens when a downstream expression expects a node/item that did not execute?
- What existing successful input is most likely to regress?
- For a bug fix, can the original failure still occur through another causal path?

Do not require a fixed number of attacks. Stop when the material risk surface is covered and additional scenarios are merely variations with no new information.

If a counterexample can be evaluated deterministically from existing artifacts, do so. If it needs runtime evidence, express it as a specific test obligation for `test-n8n-workflow`.

Read [references/regression-test-review.md](references/regression-test-review.md).

## 7. FINDINGS — record defects, not impressions

Use `assets/findings.example.json`.

Each finding must contain:

- stable ID;
- severity;
- category;
- status;
- concise defect/concern claim;
- concrete evidence;
- causal/failure scenario;
- user/system impact;
- affected requirements/invariants;
- required remediation or evidence;
- verification needed after remediation;
- confidence.

Allowed statuses:

- `OPEN`: evidence supports a current defect;
- `NEEDS_EVIDENCE`: concern is material but not yet established;
- `RESOLVED`: remediation and verification evidence are recorded;
- `ACCEPTED_RISK`: the issue remains but is explicitly accepted outside this reviewer;
- `FALSE_POSITIVE`: subsequent evidence disproved the finding.

Do not mark a finding `RESOLVED` merely because a code change was made. Resolution requires evidence appropriate to the finding.

Validate findings:

```bash
python scripts/validate_findings.py <review-dir>/findings.json
```

Read [references/severity-and-verdict.md](references/severity-and-verdict.md) before assigning `CRITICAL` or `HIGH`.

## 8. COVERAGE — prove the review covered what matters

Populate `coverage.json` with three sections:

### Acceptance criteria

Each criterion must be one of:

- `VERIFIED`
- `CONTRADICTED`
- `NOT_VERIFIED`
- `NOT_APPLICABLE`

For a behavioral workflow change, every `VERIFIED` acceptance criterion must cite at least one bound passing runtime test that explicitly declares support for that criterion. Static-only claims may use deterministic static artifacts.

### Invariants

Map every material invariant to evidence or an explicit status.

Do not infer “unchanged” merely because a node was not directly modified. Check transitive data/control dependencies where the diff can affect them.

### Review lenses

Record each required lens and the evidence/findings produced by that review.

Run:

```bash
python scripts/validate_coverage.py \
  --requirements <requirements.json> \
  --risk <review-dir>/risk-scan.json \
  --coverage <review-dir>/coverage.json \
  --bound-evidence <review-dir>/bound-test-evidence.json
```

The validator checks structural completeness and verifies that runtime evidence IDs used for coverage correspond to bound test artifacts.

## 9. VERDICT — use the mechanical gate

Do not author a favorable verdict first and then rationalize it.

Run:

```bash
python scripts/review_gate.py \
  --packet <review-dir>/review.json \
  --diff <review-dir>/workflow-diff.json \
  --risk <review-dir>/risk-scan.json \
  --findings <review-dir>/findings.json \
  --coverage <review-dir>/coverage.json \
  --bound-evidence <review-dir>/bound-test-evidence.json \
  --out <review-dir>/verdict.json
```

The gate returns exactly one of:

- `PASS`
- `PASS_WITH_CONDITIONS`
- `REJECT`
- `INSUFFICIENT_EVIDENCE`

### `PASS`

Use only when:

- the exact candidate identity is established;
- all required review lenses are complete;
- acceptance criteria and material invariants are verified or legitimately not applicable;
- behavioral changes have usable bound runtime evidence;
- no bound runtime test failed;
- no unresolved `CRITICAL` or `HIGH` finding exists;
- no material evidence gap remains;
- residual risks are low enough not to require a release condition.

### `PASS_WITH_CONDITIONS`

Use when core correctness evidence is sufficient but bounded non-critical conditions remain, such as medium-severity operational remediation or an explicitly accepted residual risk.

This is **not equivalent to release approval**. The future release skill must verify that required conditions are resolved or explicitly accepted by the appropriate human authority.

### `REJECT`

Use when evidence demonstrates a material defect, contradicted requirement/invariant, failed bound test, or unresolved high-severity issue.

### `INSUFFICIENT_EVIDENCE`

Use when the candidate cannot be bound to evidence, required runtime evidence is absent/stale/redacted/ambiguous, required review lenses are incomplete, or material requirements remain unverified.

When evidence is missing, do not downgrade the concern into a stylistic comment merely to produce a verdict.

## 10. HANDOFF — preserve review independence

After verdict:

- `PASS`: provide the review artifacts to the release process; do not deploy here.
- `PASS_WITH_CONDITIONS`: enumerate each release condition and how it must be verified.
- `REJECT` due design/implementation defect: hand specific findings to `build-n8n-workflow`.
- `REJECT` due newly discovered unexplained behavior: hand evidence to `debug-n8n-workflow`.
- `INSUFFICIENT_EVIDENCE`: hand exact missing runtime checks to `test-n8n-workflow` when authorized.

A subsequent re-review should use the new candidate fingerprint and preserve prior findings as history rather than overwriting them.

## Review packet isolation

When the execution environment supports a fresh subagent or independent review context, prefer giving that reviewer only:

- requirements/invariants;
- source workflow;
- candidate workflow;
- deterministic diff/risk outputs;
- bound test evidence;
- relevant architecture/contracts.

Do **not** lead with the implementation agent's argument for why the change is correct.

When fresh context is unavailable, use the evidence order in `RECONSTRUCT` to reduce anchoring.

## Evidence classes

Distinguish at least:

- `REQUIREMENT`: explicit user/system requirement;
- `SOURCE`: observed prior workflow behavior/configuration;
- `STATIC`: deterministic inspection/diff/validator output;
- `RUNTIME`: bound n8n execution evidence;
- `HISTORICAL`: prior known-good or known-failing execution evidence;
- `AUTHOR_CLAIM`: rationale or assertion from the change author.

`AUTHOR_CLAIM` can guide investigation but cannot by itself verify a requirement or close a finding.

## Completion report

Summarize with:

1. candidate behavior fingerprint;
2. verdict;
3. blocking findings, if any;
4. conditions, if any;
5. requirement/invariant coverage gaps;
6. bound runtime evidence used;
7. residual risks;
8. exact next handoff.

Generate a compact machine-derived summary with:

```bash
python scripts/review_summary.py <review-dir>
```

Do not say “looks good” when the mechanical gate says otherwise.
