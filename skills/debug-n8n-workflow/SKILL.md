---
name: debug-n8n-workflow
description: "Diagnose and resolve non-trivial failures in existing n8n workflows and their connected code, data, databases, APIs, credentials, sub-workflows, or runtime. Use when a workflow errors, produces wrong or inconsistent output, behaves intermittently, regresses, or a previous fix did not fully solve the problem. Investigate from evidence, establish the complete material causal set, design the smallest robust fix, and verify it with real n8n execution evidence. Do not use for ordinary new-feature implementation with no unexplained existing failure."
---

# Debug n8n Workflow

Treat debugging as causal investigation, not patch-and-test iteration.

The objective is not a plausible fix. Explain the observed failure, identify the complete **material causal set**, make the smallest robust change that addresses it, and prove the result with representative execution evidence.

## Non-negotiable rules

1. Preserve the failing state before material changes: workflow/config snapshot, execution evidence, failure signature, and relevant input.
2. Separate `OBSERVED`, `TESTED`, `INFERRED`, and `ASSUMED`. Do not present inference as observation.
3. Prefer evidence from the actual failing execution and a comparable known-good execution over generic reasoning.
4. Do not call a visible exception or downstream symptom the root cause until its generating mechanism is established.
5. Finding one cause does not close the investigation while another material mechanism could independently recreate the failure.
6. Prefer non-mutating, reversible, high-information experiments. Change one causal variable at a time when feasible.
7. If evidence contradicts the current model, update the model. Do not protect a favored hypothesis with ad-hoc assumptions.
8. Do not stack speculative patches. A changed error message is evidence, not success.
9. Prefer the smallest reversible fix that fully addresses the confirmed causal set and preserves required behavior. No opportunistic refactors.
10. Local tests are insufficient when the relevant behavior depends on hosted n8n semantics, configuration, credentials, integrations, retries, state, or concurrency.
11. Never extract, print, persist, or copy plaintext credential secrets. Record credential references only.
12. Do not run mutating diagnostic experiments against production side effects when a safe development/test path can answer the question.
13. Keep rigor proportional. If direct evidence mechanically proves a simple cause, do not invent hypotheses merely to satisfy a process.

## Persistent case state

For every non-trivial investigation, create a durable case ledger:

```bash
python scripts/init_case.py --root .agent-cases --title "<short problem>"
```

Read `references/case-ledger.md` for the file contracts. Keep hypotheses, experiments, evidence, causal conclusions, and verification in the case files rather than conversational memory.

Use this lifecycle:

`BASELINE -> MODEL -> HYPOTHESES -> EXPERIMENTS -> CAUSAL_CLOSURE -> FIX_DESIGN -> IMPLEMENT -> VERIFY -> CLOSE`

New evidence may move the case backward. Before advancing, run:

```bash
python scripts/case_gate.py <case-dir> --to <STAGE>
```

The gate verifies structural prerequisites; it does not replace engineering judgment.

## 1. BASELINE — define the defect

Before explaining why:

- read repository `AGENTS.md` and only relevant project docs;
- identify target environment, workflow, execution, and relevant versions/settings;
- capture current workflow/config and failing execution before modification;
- define exact observed behavior, expected behavior, input conditions, impact, and reproduction pattern;
- find a comparable known-good execution when available;
- record material unknowns rather than silently assuming answers.

Define the **failure signature** at the narrowest useful semantic level. Prefer “item 4 loses `fund_id` between X and Y” over “workflow fails.”

If the workflow is actively causing material harm, corruption, duplicate external actions, or uncontrolled cost, a reversible `CONTAINMENT` action may precede full diagnosis. Preserve evidence first when possible, minimize scope, and resume diagnosis. Containment is not root-cause resolution.

## 2. MODEL — build the causal map

Build the smallest model capable of explaining the failure. Use an **expanding causal cone**:

1. start at the observed failure or first known divergence;
2. trace upstream to stable input/system-of-record boundaries;
3. trace downstream to the impact boundary;
4. expand sideways only when evidence implicates branches, sub-workflows, state, concurrency, credentials, runtime, or external dependencies.

Record the relevant graph, data contracts, transformations, expressions, Code-node logic, state/database operations, external dependencies, side effects, retry/idempotency behavior, timing/concurrency assumptions, and material versions/settings in `system_model.json`.

Do not map the entire platform without evidence that it matters.

If item mapping, expressions, Merge/loop behavior, Code nodes, or cross-node references are implicated, read `references/n8n-semantics.md`.

## 3. HYPOTHESES — explain the mechanism

When the cause is not mechanically proven, read `references/failure-taxonomy.md` and `references/causal-investigation.md`.

Create enough **mutually distinct causal hypotheses** to cover the plausible failure classes. Do not target an arbitrary number such as 20. Difficult ambiguous incidents often need roughly 5–10 initially; expand only when evidence does not discriminate.

Every hypothesis must state:

- the causal mechanism;
- affected component(s);
- how it produces the exact failure signature;
- evidence for and against;
- predicted observations;
- best discriminating test;
- whether it could independently cause the incident;
- current state.

Allowed states: `ACTIVE`, `CONFIRMED_CAUSE`, `CONTRIBUTING_CAUSE`, `CONSEQUENCE`, `RULED_OUT`, `SUBSUMED`, `UNRESOLVED`.

Before the first mutating experiment, perform an anti-anchoring pass:

- What if the obvious explanation is false?
- Is the visible error downstream from the first semantic divergence?
- Could data shape, state, environment, timing, or concurrency mimic the symptom?
- Which assumed similarity between failing and successful cases has not been verified?
- Could multiple defects interact?

Add hypotheses only for genuinely distinct mechanisms.

## 4. EXPERIMENTS — reduce uncertainty efficiently

Read `references/experiment-design.md` for ambiguous cases.

Choose the next experiment by **diagnostic information gained relative to risk, cost, and system disturbance**, not only by which hypothesis seems most likely.

Prefer, in order where useful:

- existing evidence inspection;
- failing-vs-known-good differential analysis;
- static graph/config/code inspection;
- exact failing-fixture replay;
- one-variable substitution;
- subgraph isolation/bisection;
- controlled dependency substitution;
- safe fault-injection or repeated timing/concurrency tests.

Before each material experiment record what hypotheses it discriminates, what is controlled, predicted outcomes, and side-effect risk. Afterward record the actual result and update the hypothesis ledger.

If a surprising result invalidates the model, return to `MODEL` or `HYPOTHESES` rather than adding another patch.

## 5. CAUSAL_CLOSURE — establish what actually caused it

Read `references/causal-investigation.md`.

A permanent root-cause claim should ordinarily have:

- **localization** of the first relevant divergence/condition;
- a technically coherent **mechanism**;
- evidence that the mechanism exists in the actual failing case;
- discrimination from serious competing explanations;
- counterfactual/intervention evidence when safe, or an explicit reason why equivalent evidence is the strongest available.

After confirming one cause, re-evaluate all remaining material hypotheses.

Move to fix design only when every plausible material hypothesis capable of independently recreating the failure is confirmed/contributing, ruled out, or subsumed. A residual unresolved item may remain only when it cannot materially invalidate the fix; document the rationale and risk.

Populate `causal_set.json`. Do not claim philosophical certainty; establish closure over the material hypothesis space supported by the system model and evidence.

## 6. FIX_DESIGN — choose the smallest robust intervention

Read `references/fix-selection.md`.

Generate multiple options only when a real technical trade-off exists. For each serious option assess causal coverage, invariants, blast radius, compatibility, migration need, new failure modes, reversibility, and testability.

Select in this order:

1. addresses the complete confirmed causal set;
2. preserves required invariants;
3. minimizes semantic blast radius;
4. is reversible;
5. is simple to reason about and test;
6. avoids architectural change unless architecture is itself causal or makes a local fix brittle/unsafe.

Define acceptance tests before implementation.

## 7. IMPLEMENT — change only what is justified

- preserve an exact pre-change snapshot;
- implement only the selected fix;
- record each changed node/file/configuration and its causal justification;
- keep unrelated cleanup out of the patch;
- use a safe development/test workflow for mutating changes whenever possible;
- if implementation exposes an incorrect causal assumption, stop and return to investigation.

Do not “fix forward” by layering changes until something happens to pass.

## 8. VERIFY — prove behavior in the right environment

Read `references/live-test-protocol.md`. If credentials, sensitive data, or external writes are involved, also read `references/security-and-side-effects.md`.

Verification must prove semantic behavior, not merely absence of an exception.

At minimum when applicable run:

1. the exact original failing fixture;
2. at least one representative historical known-good fixture;
3. the nearest relevant boundary/negative case around the root cause.

Add only mechanism-relevant cases such as null/empty values, 0/1/many items, retries/duplicates, concurrency/order, API failures, schema variation, alternate branches, or large inputs.

If the defect depends on n8n execution semantics, node behavior, integrations, workflow settings, runtime version, state, retries, or concurrency, verify in a representative n8n development/test runtime when access permits. Inspect relevant node-level outputs/state and assertions, not only final workflow status.

If hosted behavior differs from local behavior, preserve that execution as new evidence and reopen the investigation.

Record the environment, fixtures, assertions, outcomes, and evidence in `verification.json`.

## 9. CLOSE — preserve the learning

Close only when:

- the original failure signature is explained;
- the material causal set is documented;
- the fix addresses that set;
- representative verification passes;
- relevant regressions pass;
- residual risks and untested assumptions are explicit.

Write `closeout.md` with the causal chain, key evidence, exact change, verification, residual risks, and durable regression fixture(s) added or recommended.

If the incident exposed a recurring agent/system weakness, prefer improving in this order:

`regression test -> deterministic tool -> lint/invariant -> project documentation -> existing Skill -> new Skill`.

## Reference routing

Read only what the current case needs:

- `references/case-ledger.md` — durable case state and field contracts.
- `references/failure-taxonomy.md` — broaden an ambiguous hypothesis space.
- `references/causal-investigation.md` — evidence strength, multiple causes, contradiction handling.
- `references/experiment-design.md` — efficient discriminating tests.
- `references/n8n-semantics.md` — n8n item/expression/flow/runtime-specific checks.
- `references/live-test-protocol.md` — safe hosted-n8n verification.
- `references/fix-selection.md` — robust minimal-change choice.
- `references/security-and-side-effects.md` — credentials, permissions, sensitive data, external writes.

## Reporting

Report concisely but evidence-first: failure, confirmed cause(s), decisive evidence, exact change, verification, and remaining uncertainty. Keep the full investigative record in the case ledger rather than dumping it into the user response.
