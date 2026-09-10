# Remediation hierarchy

Prefer stronger, cheaper, more local controls.

## 1. Regression fixture / test
Use when the failure can be represented reproducibly. This is usually required even when another remediation is selected.

## 2. Deterministic checker / tool
Use when the decision is structural, calculable, inspectable, or safety-critical. Good tools return stable JSON/text, distinguish PASS/FAIL/UNKNOWN, and use meaningful exit codes.

## 3. Environment / observability
Use when the model lacks access to runtime truth: versions, logs, schemas, execution IDs, state, API capabilities, or external effects.

## 4. Repository knowledge / AGENTS map
Use for durable facts, routing, ownership, invariant summaries, and pointers. Keep the entry map short; deeper material belongs in structured docs/references.

## 5. Existing Skill update
Use when non-obvious procedural judgment belongs to an existing intent and cannot be fully reduced to a deterministic tool.

## 6. New Skill
Use only when there is a distinct user intent and lifecycle with independent value and clear routing.

## Selection criteria

Evaluate:

- causal coverage;
- determinism;
- generality beyond one case;
- false-positive/false-block risk;
- blast radius;
- maintenance burden;
- agent context cost;
- reversibility;
- security impact.

Do not add prose merely because it is easier to edit than the underlying harness.
