# Performance and observability review

## Performance

Review performance only when the change can materially alter work volume or latency, for example:

- new loops or fan-out;
- remote request inside per-item processing;
- repeated database queries;
- large aggregation in Code nodes;
- changed batching/concurrency;
- payload growth or binary-data handling.

Estimate using expected cardinality, not a one-item fixture. Require measurement when expected scale is material and the cost cannot be bounded statically.

## Observability

A side effect should leave enough evidence to answer whether it actually occurred. Check for stable correlation identifiers across important boundaries.

For failure handling, verify that operators can distinguish:

- success;
- retryable failure;
- permanent failure;
- partial completion;
- skipped/filtered input;
- human-review state where applicable.

Do not require verbose logging of every field. Prefer structured identifiers, stage/status, timestamps, destination IDs, and error class while excluding secrets/sensitive payloads.

## False observability

Execution `success` is not sufficient when downstream writes can fail silently or errors are intentionally tolerated. Review the actual evidence contract after a side effect.
