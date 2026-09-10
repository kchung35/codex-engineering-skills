# Severity and verdict model

## Severity

### CRITICAL

Use for a credible path to severe unauthorized action, broad secret exposure, destructive production mutation, systemic data corruption/loss, or another failure whose impact is unacceptable without immediate blocking.

### HIGH

Use for material required-behavior failure, duplicate/lost writes, broken idempotency on an important operation, major integration/security regression, incorrect cross-workflow contract, or a defect likely to make the workflow substantially wrong in normal or realistically adverse operation.

### MEDIUM

Use for bounded robustness, recoverability, observability, maintainability, or performance issues that matter operationally but do not invalidate the primary required behavior under ordinary conditions.

### LOW

Use for minor maintainability, readability, documentation, or low-impact resilience issues.

### INFO

Use for non-blocking observations that may help future engineering work. Do not inflate INFO items into defects.

## Confidence

- `HIGH`: direct static/runtime evidence strongly supports the claim.
- `MEDIUM`: evidence supports the mechanism but some uncertainty remains.
- `LOW`: plausible concern requiring additional evidence.

A low-confidence material concern should usually use `NEEDS_EVIDENCE` rather than `OPEN`.

## Verdict precedence

1. Demonstrated material defect or contradicted requirement/invariant -> `REJECT`.
2. Material evidence gap, stale/unbound runtime evidence, or incomplete required lens -> `INSUFFICIENT_EVIDENCE`.
3. Core correctness verified but bounded medium/accepted residual conditions remain -> `PASS_WITH_CONDITIONS`.
4. Requirements/invariants verified, required lenses reviewed, behavioral runtime evidence bound and passing, and no blocking findings -> `PASS`.

Do not use a numeric score to override these gates. Severity and evidence are not additive points.
