# Smoke-test safety

A production smoke test is a real production action unless proven otherwise.

Do not use a smoke test that:

- emails or messages real users unexpectedly;
- creates real financial/legal/customer records;
- causes irreversible external effects;
- mutates shared state without a deterministic cleanup/idempotency strategy;
- bypasses ordinary authorization or approval controls.

Prefer a canary tenant/account, synthetic payload, read-only path, or passive observation.

Every planned side effect must be enumerated in `postrelease-plan.json`. An unlisted side effect blocks automated smoke execution.
