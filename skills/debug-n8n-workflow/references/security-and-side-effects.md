# Security and Side-Effect Rules

## Credentials

- Never print, export, commit, or place plaintext credential values in the case ledger.
- Prefer credential IDs/names/references and permission metadata.
- Reuse existing authorized credential references only within approved environments.
- A separate test instance should use separately provisioned test credentials unless organizational tooling provides a secure supported transfer mechanism.

## Least privilege

The debugging agent should preferably have read access to production workflow/execution evidence and write/run access only to a dedicated development/test scope.

Do not compensate for missing access by broadening permissions unless explicitly authorized.

## Dangerous side effects

Identify before execution any node that can:

- send email/messages/notifications;
- create/update/delete external records;
- write to production databases;
- trigger downstream workflows/jobs;
- publish content;
- make payments/trades/orders;
- mutate files/storage;
- consume expensive external services.

Isolate or stub these unless the side effect itself is under test and the test target is safe.

## Sensitive data

Minimize copied execution payloads. Preserve only the fields needed to reproduce/diagnose the failure when sensitive production data is involved, subject to organizational policy.

## Security as a causal hypothesis

Authentication, permissions, secret rotation, credential identity, and security controls may themselves be root causes. Investigate them through metadata and controlled authenticated calls without exposing secret material.
