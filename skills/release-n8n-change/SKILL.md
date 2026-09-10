---
name: release-n8n-change
description: "Release an already-built, tested, and independently reviewed n8n workflow change into production using exact candidate binding, production drift detection, rollback capture, draft staging, explicit version publication, post-release verification, and fail-closed rollback/escalation. Use only when the user is intentionally deploying or publishing an approved n8n workflow change. Do not use to design, debug, test experimentally, or decide what the fix should be."
---

# Release n8n Change

Release exactly the reviewed candidate. Do not redesign it, diagnose it, or improve it during deployment.

This skill owns the controlled transition from **approved candidate** to **verified production publication**.

Use the lifecycle:

`INTAKE -> BIND -> PREFLIGHT -> SNAPSHOT -> STAGE -> RECHECK -> PUBLISH -> VERIFY -> CLOSE`

Any material inconsistency moves to `STOP` or `ROLLBACK`; it does not trigger improvisational patching.

## Non-negotiable rules

1. Release only an artifact that has already passed `review-n8n-change` with `PASS`, or `PASS_WITH_CONDITIONS` where every release-blocking condition is resolved.
2. Bind the release to the exact candidate behavioral fingerprint reviewed. A changed candidate requires new test/review evidence.
3. Bind the release to the expected production source state. Any unexplained production drift blocks release.
4. Release one workflow per release case by default. Multi-workflow releases require an explicit dependency/order plan and separate bindings per workflow.
5. Capture the production workflow, current draft fingerprint/version, current published `activeVersionId`, settings relevant to runtime behavior, and rollback target before the first production mutation.
6. Never update a published workflow using n8n's default auto-publish behavior. Stage with `publishIfActive=false`.
7. Publish an explicit staged `versionId`. Never publish an unspecified "latest" draft in an automated release.
8. Re-fetch and verify the staged draft immediately before publication. If its fingerprint or version changed, stop.
9. A successful API response is not proof that the intended version is live. Verify `activeVersionId` equals the staged version.
10. Runtime/post-release evidence must be bound to the published candidate version where the available execution metadata permits this.
11. Production smoke tests must have an explicit side-effect policy. Do not create real emails, trades, approvals, irreversible writes, or customer-facing actions merely to prove deployment.
12. Prefer passive verification or a safe synthetic canary when a production trigger has meaningful side effects.
13. If post-release verification reveals a material regression and rollback criteria are met, restore the captured prior published version rather than inventing a hotfix.
14. If the workflow was originally unpublished, rollback means unpublish it again.
15. Runtime rollback and draft restoration are separate concerns. Restore the prior published version first; do not overwrite the current draft unless explicitly planned.
16. Do not expose API keys, passwords, tokens, credential values, or sensitive execution payloads in release artifacts or source control.
17. Do not use production execution data to broaden the task. Unexpected behavior after release is evidence for `debug-n8n-workflow`, not permission to edit production.
18. Preserve an auditable release record: who/what approved, what candidate was bound, what production baseline was observed, what version was staged/published, what verification ran, and whether rollback occurred.
19. Treat ambiguous state as failure to prove release safety. `UNKNOWN` is not `PASS`.
20. Never bulk publish/unpublish workflows as part of this skill.

## 1. INTAKE — establish the release object

Create a release case directory, for example:

```text
.release-cases/REL-2026-09-10-001/
```

Start from:

- `assets/release-config.example.json`
- `assets/review-verdict.example.json`
- `assets/release-plan.example.json`
- `assets/rollback-plan.example.json`
- `assets/postrelease-plan.example.json`

The release must identify:

- production n8n base URL;
- workflow ID;
- candidate workflow JSON path;
- candidate behavioral fingerprint;
- reviewed candidate fingerprint;
- expected pre-release source fingerprint;
- expected pre-release `activeVersionId` if known;
- release intent (`PUBLISH_CHANGE` or `PUBLISH_PREVIOUSLY_UNPUBLISHED`);
- required review verdict;
- rollback policy;
- post-release verification policy.

Do not infer production workflow IDs from names when a stable ID is available.

Read [references/release-safety-model.md](references/release-safety-model.md).

## 2. BIND — prove the artifacts refer to the same change

Compute the candidate fingerprint:

```bash
python scripts/fingerprint_workflow.py candidate.json
```

Then validate that:

- candidate fingerprint == release-plan candidate fingerprint;
- candidate fingerprint == review verdict candidate fingerprint;
- review verdict is acceptable;
- all release-blocking review conditions are resolved;
- the review evidence is not explicitly stale;
- the workflow ID in all release artifacts is identical.

Run:

```bash
python scripts/release_preflight.py \
  --config release-config.json \
  --plan release-plan.json \
  --review review-verdict.json \
  --candidate candidate.json
```

Any mismatch blocks release.

Read [references/candidate-binding.md](references/candidate-binding.md).

## 3. PREFLIGHT — verify the production target before touching it

The production target must be explicitly allowlisted in `release-config.json`.

Require:

- `environment_class = "PRODUCTION"`;
- exact expected host or approved host suffix;
- API key read from an environment variable, never embedded in JSON;
- required workflow ID;
- bounded request timeout;
- publication permission expected;
- rollback plan present;
- post-release verification plan present.

Before mutation, perform a read-only API check:

```bash
python scripts/capture_baseline.py \
  --config release-config.json \
  --plan release-plan.json \
  --out production-baseline.json
```

The baseline capture must fetch the exact workflow and record at least:

- workflow ID/name;
- current draft `versionId`;
- current draft behavioral fingerprint;
- current `activeVersionId`;
- whether the workflow is currently published;
- relevant workflow settings;
- capture timestamp;
- full rollback snapshot or a path/hash to it.

If the production source fingerprint does not match the release plan's expected source fingerprint, stop with `PRODUCTION_DRIFT`.

If an expected pre-release `activeVersionId` was provided and it does not match, stop.

Read [references/drift-detection.md](references/drift-detection.md).

## 4. SNAPSHOT — establish a deterministic rollback target

Before staging, the release record must answer:

> Exactly what runtime publication state will be restored if this release fails?

For an already-published workflow, capture:

```text
rollback_kind: PUBLISH_VERSION
rollback_version_id: <original activeVersionId>
```

For an originally unpublished workflow:

```text
rollback_kind: UNPUBLISH
```

Store the current full workflow snapshot as an additional forensic/recovery artifact, but do not confuse the current draft `versionId` with the current published `activeVersionId`.

The preferred runtime rollback is **publication state restoration**, not blind replacement of the draft.

Run the gate before staging:

```bash
python scripts/release_gate.py <release-dir> --to STAGE
```

Read [references/rollback.md](references/rollback.md).

## 5. STAGE — save the candidate as a draft only

Use the public API update operation with:

```text
publishIfActive=false
```

This is mandatory because current n8n behavior may automatically republish an updated workflow when it is already published if that flag is omitted or true.

Stage with:

```bash
python scripts/stage_candidate.py \
  --config release-config.json \
  --plan release-plan.json \
  --baseline production-baseline.json \
  --candidate candidate.json \
  --out staged-release.json
```

The stage operation must:

1. re-fetch production immediately before update;
2. verify the pre-release fingerprint and `activeVersionId` still match the baseline;
3. update with `publishIfActive=false`;
4. capture the returned draft `versionId`;
5. verify the returned/current draft fingerprint equals the approved candidate fingerprint;
6. verify the live `activeVersionId` still equals the original value;
7. persist the staged version ID.

If staging unexpectedly changes the published version, classify as `UNEXPECTED_PUBLICATION` and stop/rollback according to policy.

Read [references/n8n-publication-semantics.md](references/n8n-publication-semantics.md).

## 6. RECHECK — eliminate the race between staging and publication

Immediately before publication, re-fetch the workflow again.

Require all of:

- workflow ID unchanged;
- current draft `versionId` == staged version ID;
- current draft fingerprint == approved candidate fingerprint;
- `activeVersionId` still equals the captured baseline value;
- no unresolved release-blocking condition has appeared;
- no operator/agent has changed the candidate in place.

Run:

```bash
python scripts/verify_staged.py \
  --config release-config.json \
  --baseline production-baseline.json \
  --staged staged-release.json \
  --candidate candidate.json
```

Failure here is not a reason to restage automatically. Stop and investigate the drift.

## 7. PUBLISH — publish the exact version, once

Publish only the staged version ID:

```bash
python scripts/publish_candidate.py \
  --config release-config.json \
  --baseline production-baseline.json \
  --staged staged-release.json \
  --out publication.json
```

The script must send an explicit `versionId` to the publication endpoint.

Do not publish with an omitted version ID.

After the API call, poll/read the workflow until one of these occurs:

- `activeVersionId == staged_version_id` -> publication state confirmed;
- timeout -> `PUBLICATION_UNCONFIRMED`;
- another unexpected `activeVersionId` appears -> `WRONG_VERSION_LIVE`.

Do not classify HTTP 200 alone as release success.

n8n publication can involve trigger reconciliation. Treat publication confirmation and behavioral verification as separate gates.

## 8. VERIFY — prove production is behaving as intended

Verification has three layers.

### Layer A — control-plane verification

Require:

- workflow exists;
- `activeVersionId` == staged version ID;
- current draft fingerprint still matches the approved candidate;
- expected trigger/publication state is present where observable;
- no unexpected workflow drift occurred after publication.

Run:

```bash
python scripts/verify_publication.py \
  --config release-config.json \
  --staged staged-release.json \
  --candidate candidate.json \
  --out control-plane-verification.json
```

### Layer B — runtime verification

Choose the safest adequate strategy from `postrelease-plan.json`:

- `PASSIVE`: observe naturally occurring executions;
- `SAFE_CANARY`: trigger an explicitly side-effect-safe synthetic execution;
- `BOUND_PRODUCTION_SMOKE`: run an explicitly approved bounded production path;
- `CONTROL_PLANE_ONLY`: allowed only when runtime execution is impossible or unjustifiably risky, and must result in a qualified/limited closeout rather than pretending behavior was proved.

For runtime verification, prefer the established `test-n8n-workflow` evidence machinery where it can safely bind execution evidence to the published workflow/version.

Check:

- execution status;
- `workflowVersionId` where available;
- required acceptance criteria;
- expected output/side-effect evidence;
- unexpected errors/retries;
- regression indicators defined in the release plan.

### Layer C — operational verification

For changes affecting triggers, credentials, schedules, queues, state, or external writes, check the specific operational invariant named in the plan.

Examples:

- schedule remains correct;
- webhook still resolves;
- duplicate prevention still holds;
- no backlog/retry storm appears;
- no new authorization failures appear;
- expected downstream write count is bounded.

Read:
- [references/post-release-verification.md](references/post-release-verification.md)
- [references/smoke-test-safety.md](references/smoke-test-safety.md)

## 9. ROLLBACK — restore known state, do not hotfix

Rollback is triggered by the explicit criteria in `rollback-plan.json`.

Typical automatic/strong rollback conditions:

- wrong version is live;
- candidate publication cannot be confirmed within bounded time and system state is inconsistent;
- CRITICAL/HIGH regression in the defined release surface;
- unsafe duplicate/external write behavior;
- trigger registration failure that makes the workflow unavailable;
- catastrophic error-rate/retry storm attributable to the release.

Run:

```bash
python scripts/rollback_release.py \
  --config release-config.json \
  --baseline production-baseline.json \
  --publication publication.json \
  --out rollback-result.json
```

If the workflow was previously published, publish the captured **original `activeVersionId`** explicitly.

If it was previously unpublished, unpublish it.

After rollback, verify the runtime publication state was restored.

Do not automatically restore/overwrite the draft candidate unless the rollback plan specifically requires it.

If rollback itself cannot be confirmed, classify as `ROLLBACK_UNCONFIRMED` and escalate immediately. Do not continue experimenting.

Read [references/rollback.md](references/rollback.md) and [references/incident-escalation.md](references/incident-escalation.md).

## 10. CLOSE — record what actually happened

A successful release may close only when:

- approved candidate fingerprint was bound;
- production baseline matched expectations;
- rollback target was captured;
- candidate was staged without unintended publication;
- exact staged version was published;
- `activeVersionId` was verified;
- required post-release verification passed or an explicitly limited verification mode was documented;
- no release-blocking issue remains;
- release artifacts contain no secrets.

Use:

```bash
python scripts/release_gate.py <release-dir> --to CLOSE
python scripts/release_summary.py <release-dir>
```

Allowed terminal outcomes:

- `RELEASED_VERIFIED`
- `RELEASED_LIMITED_VERIFICATION`
- `ROLLED_BACK_VERIFIED`
- `STOPPED_BEFORE_PUBLICATION`
- `ROLLBACK_UNCONFIRMED`

Never use `SUCCESS` as a vague catch-all.

## Release case structure

Recommended:

```text
.release-cases/REL-.../
├── release-config.json
├── release-plan.json
├── review-verdict.json
├── rollback-plan.json
├── postrelease-plan.json
├── candidate.json
├── candidate-fingerprint.json
├── production-baseline.json
├── source-workflow-snapshot.json
├── staged-release.json
├── publication.json
├── control-plane-verification.json
├── runtime-verification.json
├── rollback-result.json
├── release-state.json
└── closeout.md
```

Keep secrets outside this directory.

## State machine

The release state machine is deliberately strict:

```text
PREPARED
   |
   v
BASELINED
   |
   v
STAGED
   |
   v
PUBLISHED
   |
   +-----------> ROLLBACK_REQUIRED -> ROLLED_BACK
   |
   v
VERIFIED
   |
   v
CLOSED
```

`STOPPED` may occur before publication at any failed safety gate.

Do not skip from `PREPARED` to `PUBLISHED`.

## Handoffs

Use `build-n8n-workflow` when the desired candidate must change.

Use `test-n8n-workflow` when additional controlled runtime evidence is needed.

Use `review-n8n-change` when candidate content changed or review evidence is stale/insufficient.

Use `debug-n8n-workflow` when production behavior is unexplained.

This release skill does not absorb those responsibilities.
