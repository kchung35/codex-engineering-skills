# Evidence and candidate binding

## Why binding matters

A runtime test is only relevant to the reviewed candidate if the behavior tested corresponds to the same candidate semantics. Timestamps, names, and verbal claims are weak provenance.

Use `behavior_sha256` from `fingerprint_workflow.py` to bind candidate and test-plan source snapshots.

## Behavioral fingerprint

The fingerprint intentionally ignores editor-only fields such as node position and notes, but includes runtime-relevant node configuration, connections, workflow settings, static state, and pinned data where present.

The artifact fingerprint also removes volatile server metadata so two exports of the same saved candidate can still be compared meaningfully.

## Test evidence states

- `BOUND_PASS`: test plan source fingerprint matches candidate and result passed.
- `BOUND_FAIL`: test plan source matches candidate and result failed.
- `STALE`: source fingerprint differs from candidate.
- `UNREADABLE`: required artifacts are missing or malformed.
- `NOT_RUNTIME`: evidence did not execute behavior, such as snapshot-only capture.

Only `BOUND_PASS` can satisfy a runtime verification obligation.

A `BOUND_FAIL` is negative evidence and should normally reject the candidate until explained or superseded by a new candidate/test.

## Redaction and truncation

If an assertion or review depends on execution data that is redacted, truncated, ambiguous, or unavailable, record the criterion as `NOT_VERIFIED`. Do not infer the missing data from final execution status.

## Evidence freshness after remediation

Any behavioral remediation creates a new candidate fingerprint. Prior test evidence becomes stale unless the behavioral fingerprint remains identical. Rebind evidence after every material candidate change.
