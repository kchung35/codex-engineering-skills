# Regression and evaluation

Every harness improvement needs a before/after evaluation plan.

## Deterministic components

Use deterministic fixtures and assertions. Required cases should produce exact expected statuses/fields where practical.

## Model-dependent components

Use the same prompt/task/evidence conditions before and after. Run multiple trials when variance can change the conclusion. Avoid comparing one lucky after-run to one unlucky baseline.

## Case sets

Include:

- `failing_cases`: historical/minimized examples the change must fix;
- `control_cases`: representative unaffected tasks that must remain correct;
- `safety_cases`: cases that must continue to block or require approval;
- optional `stress_cases`: ambiguity, scale, or boundary cases.

## Metrics

Each metric needs a direction and threshold. Examples:

- routing_accuracy: maximize;
- historical_failure_pass_rate: maximize to 1.0;
- false_block_rate: minimize;
- stale_evidence_acceptance: target 0;
- unsafe_mutation_acceptance: target 0;
- manual_interventions: minimize only if correctness/safety preserved.

A protected metric cannot materially regress just because the primary metric improved.
