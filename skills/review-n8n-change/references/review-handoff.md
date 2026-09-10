# Review handoff contract

Keep handoffs narrow and evidence-based.

## To build-n8n-workflow

Send:

- finding ID and severity;
- exact candidate fingerprint;
- violated requirement/invariant;
- evidence and failure scenario;
- required remediation outcome;
- verification obligation.

Do not prescribe a specific patch unless the finding requires one uniquely.

## To debug-n8n-workflow

Use when review discovers behavior whose cause is not established. Send the smallest reproducer/evidence packet and avoid presenting the reviewer's suspected cause as confirmed.

## To test-n8n-workflow

Send a deterministic test obligation:

- question to answer;
- relevant candidate fingerprint;
- fixture/boundary or native-trigger requirement;
- expected observation if the concern is true/false;
- assertions needed;
- safety constraints.

## To release-n8n-change

Only hand off `PASS` or `PASS_WITH_CONDITIONS` artifacts. Include `verdict.json`, candidate fingerprint, bound test evidence, unresolved accepted risks, and release conditions.
