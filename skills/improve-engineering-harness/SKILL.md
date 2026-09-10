---
name: improve-engineering-harness
description: "Improve a Codex engineering harness from observed agent failures, repeated friction, review escapes, weak tests, routing mistakes, missing tools, or stale repository guidance. Use when the problem is the agent environment or process itself rather than n8n business logic. Prefer regression fixtures, deterministic checks, tooling, observability, and concise source-of-truth documentation over adding prompt text. Update an existing skill before creating a new one unless the missing capability has a distinct intent, procedure, tool/safety envelope, and independent value."
---

# Improve Engineering Harness

Improve the system that enables Codex to work reliably. Do not use this skill to repair the n8n workflow under investigation; use it when repeated evidence shows that the **agent harness** made good work unnecessarily hard, ambiguous, unsafe, or unverifiable.

This skill owns **harness diagnosis, remediation selection, regression design, and controlled improvement of agent-facing tooling/instructions**. It does not own n8n business-logic design, workflow debugging, live workflow experiments, approval, or production release.

Use the lifecycle:

`INTAKE -> EVIDENCE -> CLASSIFY -> CAUSAL_MODEL -> REMEDIATION -> PLAN -> IMPLEMENT -> REGRESSION -> EVALUATE -> ROLLOUT -> CLOSE`

The governing principle is:

> When an agent struggles, ask what capability, invariant, evidence path, or environment affordance is missing—and make the answer legible and enforceable.

## Non-negotiable rules

1. Diagnose the harness problem from concrete evidence. Do not add rules because a hypothetical failure seems possible.
2. A single severe structural or safety failure can justify action; ordinary friction normally needs recurrence across at least two independent cases or one reproducible deterministic failure.
3. Distinguish workflow/product defects from harness defects. If the underlying n8n behavior is wrong, route to `debug-n8n-workflow` or `build-n8n-workflow`.
4. Prefer the lowest layer that can enforce the desired invariant reliably.
5. Default remediation order is: regression fixture/test -> deterministic checker/tool -> environment/observability improvement -> repository source-of-truth documentation or `AGENTS.md` routing -> update an existing Skill -> create a new Skill.
6. Do not solve deterministic problems with prose when a deterministic check can answer them cheaply.
7. Do not solve missing information with stricter instructions when the agent simply cannot access or inspect the information.
8. Do not expand `AGENTS.md` into an encyclopedia. Keep it a short navigation/routing map; put conditional knowledge in linked sources of truth.
9. Do not duplicate the same rule across many skills unless each copy is necessary for local safety. Prefer one canonical source plus mechanical enforcement.
10. Do not create a new Skill for a stage that naturally belongs inside an existing workflow, a deterministic operation that belongs in a script, or knowledge that belongs in a reference.
11. Preserve skill routing clarity. Narrow or merge overlapping descriptions before adding another catch-all skill.
12. Every harness change must name the failure mode it addresses and the regression that proves the failure no longer occurs.
13. Evaluate both improvement and regression. A change that fixes one case but degrades unrelated representative cases is not complete.
14. Measure the smallest useful outcome. Do not optimize token count, tool calls, latency, or pass rate in isolation if doing so harms correctness or safety.
15. Never weaken safety/approval boundaries merely to reduce agent friction.
16. Keep company-specific secrets, workflow exports, internal URLs, proprietary schemas, and sensitive case payloads out of public harness repositories.
17. Treat model behavior as probabilistic. Repeated evaluation is appropriate where stochastic behavior matters; deterministic harness components should have deterministic tests.
18. Separate `OBSERVED`, `REPRODUCED`, `INFERRED`, and `ASSUMED` claims in the improvement record.
19. If the proposed change cannot be evaluated, improve observability/evaluation first rather than declaring success.
20. Roll out harness changes reversibly when they can affect broad task routing or safety behavior.

## 1. INTAKE — define the harness failure precisely

Create an improvement case when one or more of these occur:

- the agent repeatedly misses the same invariant;
- a defect escapes build/test/review despite available evidence;
- a Skill routes incorrectly or two Skills overlap materially;
- the agent repeatedly performs a deterministic inspection manually and inconsistently;
- required information exists but is difficult for the agent to discover;
- a tool/environment limitation causes repeated workarounds;
- a safety boundary depends only on prose and fails or nearly fails;
- test evidence is difficult to bind, interpret, or reproduce;
- repository guidance is stale, duplicated, contradictory, or too large;
- a recurring manual intervention could become a reliable agent-facing capability.

Initialize:

```bash
python scripts/init_improvement.py \
  --title "<short failure statement>" \
  --root .agent-harness
```

The case directory contains:

```text
.agent-harness/<case-id>/
  case.json
  signals.jsonl
  classification.json
  causal-model.json
  proposal.json
  evaluation-plan.json
  evaluation.json
  rollout.json
  closeout.md
  artifacts/
```

A useful failure statement describes the observed agent behavior and consequence, not the desired solution.

Bad:
> Add a better prompt about item linking.

Better:
> In three debugging cases the agent treated output values as correct while failing to inspect item lineage, causing downstream expression failures to be mislocalized.

Read [references/evidence-and-recurrence.md](references/evidence-and-recurrence.md).

## 2. EVIDENCE — build the minimum representative corpus

Record each signal in `signals.jsonl` with:

- case/source identifier;
- task intent;
- agent action or omission;
- observable consequence;
- whether the behavior is reproducible;
- relevant Skill/tool/environment state;
- epistemic status;
- sensitive-data handling note.

Use `assets/improvement-case.example.json` as a shape reference for the aggregate case.

Do not paste entire conversations or workflow payloads when a minimized reproducer or structured summary is sufficient.

Before proposing a harness change, ask:

1. Is the failure actually in the harness?
2. Is the evidence representative rather than one malformed prompt?
3. Is there a deterministic reproducer?
4. What currently prevents the agent from succeeding?
5. Which successful cases must remain unaffected?

Run:

```bash
python scripts/validate_case.py <case-dir>/case.json
```

## 3. CLASSIFY — identify the missing capability layer

Classify the primary harness failure using `scripts/classify_failure.py` and [references/harness-failure-taxonomy.md](references/harness-failure-taxonomy.md).

Primary categories:

- `ROUTING_AMBIGUITY`: wrong Skill selected, overlapping descriptions, unclear ownership.
- `CONTEXT_DISCOVERY`: relevant source exists but is hard to find or loaded too late.
- `KNOWLEDGE_STALENESS`: instructions/docs disagree with current system behavior.
- `MISSING_INVARIANT`: an important always-applicable rule is absent or unenforced.
- `DETERMINISTIC_REASONING_GAP`: the agent repeatedly computes/inspects something a script could decide.
- `TOOL_CAPABILITY_GAP`: the agent lacks a callable capability required for the task.
- `ENVIRONMENT_LEGIBILITY`: logs, state, versions, schemas, or runtime behavior are not inspectable enough.
- `FEEDBACK_LOOP_GAP`: failures are discovered too late or evidence does not return to the agent.
- `TEST_COVERAGE_GAP`: a missing fixture/assertion allowed regression or false confidence.
- `EVIDENCE_BINDING_GAP`: tests/reviews/releases are not bound to the exact artifact.
- `SAFETY_ENFORCEMENT_GAP`: a safety property relies on discretion or prose instead of a gate.
- `SKILL_SCOPE_GAP`: an existing Skill is missing a procedure genuinely within its intent.
- `SKILL_OVERLAP`: multiple Skills claim substantially the same user intent/procedure.
- `MODEL_INTERFACE_GAP`: unstructured inputs/outputs make otherwise capable reasoning unreliable.
- `PROCESS_GAP`: ordering or handoff between existing capabilities is unclear.

Classification is a hypothesis about the harness mechanism, not merely a label.

## 4. CAUSAL_MODEL — explain why the harness produced the failure

Write `causal-model.json` before selecting a remediation for non-trivial cases.

Model the smallest chain that explains the failure:

```text
trigger/task condition
  -> missing or misleading harness affordance
  -> agent decision/action
  -> escaped check or unavailable evidence
  -> observed consequence
```

Separate:

- proximate agent mistake;
- harness condition that made the mistake likely or invisible;
- latent conditions that amplified impact;
- downstream consequence.

Do not stop at “the model ignored the instruction” when the instruction was duplicated, buried, unverifiable, contradicted by tooling, or asking the model to perform a deterministic task manually.

For ambiguous cases, maintain 2–5 plausible harness mechanisms and use existing cases or small reproductions to discriminate them. Before selecting a remediation, set `causal-model.status` to `SUFFICIENT_FOR_REMEDIATION` only when the material mechanism is supported well enough that the proposed control can be evaluated against it.

Read [references/causal-harness-analysis.md](references/causal-harness-analysis.md).

## 5. REMEDIATION — choose the lowest reliable control

Generate `proposal.json` from `assets/remediation-proposal.example.json`.

Run:

```bash
python scripts/select_remediation.py \
  --classification <case-dir>/classification.json \
  --out <case-dir>/remediation-candidates.json
```

Then choose the smallest remediation that addresses the confirmed mechanism.

### Preferred control hierarchy

1. **Regression fixture/test** — preserve a known failure so it cannot silently return.
2. **Deterministic checker or script** — encode repeatable structural/semantic decisions.
3. **Environment/tool/observability improvement** — make required state directly inspectable or actionable.
4. **Repository source-of-truth / AGENTS routing improvement** — make durable knowledge discoverable.
5. **Update an existing Skill** — add non-obvious procedural judgment that belongs to its intent.
6. **New Skill** — only for a distinct, independently useful procedural capability.

Use a stronger control earlier in the hierarchy when it can solve the same problem without unacceptable cost or rigidity.

Read [references/remediation-hierarchy.md](references/remediation-hierarchy.md) and [references/prompt-vs-tool.md](references/prompt-vs-tool.md).

## 6. Decide whether a new Skill is justified

Before selecting `NEW_SKILL`, run:

```bash
python scripts/skill_boundary_check.py <proposal.json>
```

A new Skill should normally satisfy all of these:

- distinct user intent;
- materially different procedure/lifecycle;
- meaningfully different tools/resources **or** safety/permission envelope;
- useful independently of another Skill;
- not merely a stage in an existing Skill;
- not primarily a deterministic operation better implemented as a script;
- not primarily reference knowledge;
- routing description can be made precise without overlapping existing Skills.

If these are not true, prefer an existing Skill update, script, reference, or AGENTS/doc change.

When editing Skill descriptions, run:

```bash
python scripts/detect_skill_overlap.py <skills-dir> --threshold 0.45
```

Treat lexical overlap as a routing signal, not proof of semantic duplication.

Read [references/skill-boundaries.md](references/skill-boundaries.md).

## 7. PLAN — define success before editing the harness

Create `evaluation-plan.json` before implementation.

Include:

- exact failure mechanism being addressed;
- affected harness components;
- representative failing fixtures/cases;
- representative unaffected/control cases;
- deterministic assertions where possible;
- stochastic trials where model behavior matters;
- primary success metric;
- safety/non-regression metrics;
- acceptance thresholds;
- rollback trigger;
- expected blast radius.

Do not use only the original failure case. Include at least one control case for any change that can affect broad routing or shared behavior.

Run:

```bash
python scripts/validate_proposal.py \
  --case <case-dir>/case.json \
  --proposal <case-dir>/proposal.json \
  --evaluation-plan <case-dir>/evaluation-plan.json
```

Read [references/regression-and-evaluation.md](references/regression-and-evaluation.md) and [references/anti-overfitting.md](references/anti-overfitting.md).

## 8. IMPLEMENT — change the harness at the selected layer

Implement only the selected remediation and its regression coverage.

Typical targets:

### Tests / fixtures
- add minimized regression case;
- add deterministic assertion;
- add negative case for the failure mechanism.

### Scripts / tools
- return stable machine-readable output;
- fail closed for safety-critical checks;
- distinguish `UNKNOWN` from `PASS`;
- keep secrets out of output;
- make exit codes meaningful.

### AGENTS.md / repository docs
- keep AGENTS short and navigational;
- point to canonical sources of truth;
- remove obsolete/duplicated rules rather than only adding text;
- make required validation commands discoverable.

### Existing Skills
- add only non-obvious judgment/procedure;
- move deterministic logic to scripts;
- use references for conditional detail;
- preserve clear routing boundaries.

### Environment / observability
- expose versions, execution IDs, schemas, logs, metrics, or state in agent-readable form;
- prefer stable local commands/APIs over manual UI instructions when feasible.

Do not modify unrelated harness components “while here.”

## 9. REGRESSION — prove the historical failure is now mechanically represented

A harness improvement is incomplete until the original failure has a durable regression representation.

Run the relevant deterministic tests and record them in `evaluation.json`.

For broad changes, use:

```bash
python scripts/regression_gate.py \
  --plan <case-dir>/evaluation-plan.json \
  --results <case-dir>/evaluation.json
```

The regression gate must block when:

- a required historical failure still reproduces;
- a required control case regresses;
- safety-critical checks weaken;
- required results are missing or uninterpretable.

A prose statement that “the prompt is clearer now” is not a regression test.

## 10. EVALUATE — measure the change against the baseline

Use deterministic metrics where the harness component is deterministic.

For model-dependent behavior, use multiple trials when practical and compare before/after under the same task/evidence conditions.

Useful metrics may include:

- success on historical failure fixtures;
- false-positive / false-block rate;
- correct Skill routing rate;
- unresolved evidence rate;
- time/tool-call burden when correctness is unchanged;
- number of manual interventions;
- deterministic gate coverage;
- stale-doc/routing violations;
- review escapes;
- safety incidents/near misses.

Run:

```bash
python scripts/compare_evaluation.py \
  --plan <case-dir>/evaluation-plan.json \
  --before <before-results.json> \
  --after <after-results.json> \
  --out <case-dir>/evaluation-comparison.json
```

Do not accept a change solely because the targeted metric improves if a protected metric materially regresses.

## 11. ROLLOUT — apply broad harness changes reversibly

For localized regression tests or helper scripts, normal repository review may be sufficient.

For changes that affect:

- Skill routing;
- shared AGENTS instructions;
- production mutation permissions;
- security gates;
- broad execution policy;
- many repositories/users;

use an explicit rollout record and rollback path.

Prefer:

1. local/offline tests;
2. representative repository/task cases;
3. limited rollout;
4. wider adoption after evidence.

If new failures appear, revert or narrow the harness change first. Do not preserve a bad abstraction because it was expensive to build.

Read [references/rollout-and-rollback.md](references/rollout-and-rollback.md).

## 12. CLOSE — make the improvement durable

Close only when:

- the harness failure mechanism is documented;
- selected remediation addresses that mechanism;
- historical failure has durable regression coverage;
- representative controls pass;
- relevant safety properties did not weaken;
- source-of-truth/routing docs are updated if needed;
- residual risks and unsupported cases are explicit;
- rollback path exists for broad changes.

Run:

```bash
python scripts/harness_gate.py <case-dir> --to CLOSE
python scripts/harness_summary.py <case-dir>
```

The closeout should answer:

1. What repeatedly failed?
2. Why was the harness responsible?
3. Why was this remediation layer chosen?
4. What deterministic or representative regression now exists?
5. What improved, and what did not?
6. What remains intentionally outside scope?

## Failure-to-remediation examples

These are routing examples, not automatic rules.

### Repeated hidden n8n expression dependency misses

Prefer:

```text
regression fixture
+ deterministic expression/dependency auditor
```

not:

```text
longer instruction telling the model to inspect references carefully
```

### Agent tests the wrong workflow version

Prefer artifact/version fingerprint binding and a gate.

### Agent cannot infer production behavior because runtime evidence is unavailable

Prefer an environment/observability capability that exposes the evidence. Do not instruct the model to “reason more carefully.”

### Two Skills both activate for “validate this workflow”

Narrow descriptions and ownership. Merge Skills if procedures are substantially the same.

### Recurring judgment genuinely requires a new procedural lifecycle

Create a new Skill only after the boundary check passes and routing remains unambiguous.

## Handoff rules

- n8n behavior is unexplained -> `debug-n8n-workflow`
- intentional workflow design/change -> `build-n8n-workflow`
- runtime evidence required -> `test-n8n-workflow`
- independent candidate approval -> `review-n8n-change`
- production deployment -> `release-n8n-change`
- repeated failures in those capabilities or their environment -> this skill

This skill should make the five core skills **simpler over time**, not accumulate a sixth layer of duplicated instructions.
