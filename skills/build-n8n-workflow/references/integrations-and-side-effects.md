# Integrations and side effects

Treat every external node as an interface with a contract.

## Reads

Define:
- identifier/query;
- pagination;
- expected absence behavior;
- rate limits;
- timeout;
- response normalization.

## Writes

Define:
- logical operation;
- idempotency/duplicate behavior;
- provider/database response used as evidence;
- update/create semantics;
- concurrency/conflict handling;
- retry safety.

## Databases

Prefer parameterized queries. Put invariant-level correctness in database constraints when possible.

For upserts, define:
- conflict key;
- fields updated;
- fields preserved;
- event/version ordering.

## HTTP APIs

Prefer explicit method, path, parameter/body mapping, timeout, and response validation. Never assume HTTP 2xx alone proves the intended business effect when the provider returns status in the payload.

## Credentials

Workflow JSON may contain credential references; it must not contain plaintext secret material.

Do not "copy a credential" by extracting its secret. Provision credentials in the target environment and remap references.

## Side-effect manifest

For each external node record:
- node;
- system;
- operation;
- classification (`READ`, `CREATE`, `UPDATE`, `DELETE`, `SEND`, `EXECUTE`, `UNKNOWN`);
- idempotency;
- retry ownership;
- test double/lab target.

Unknown blocks closure.
