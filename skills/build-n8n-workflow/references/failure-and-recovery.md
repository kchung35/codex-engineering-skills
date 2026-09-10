# Failure and recovery

Failures should be classified by semantics, not only by node status.

## Failure classes

- invalid input / contract violation;
- authentication/authorization;
- not found / stale reference;
- rate limit;
- transient network/service failure;
- deterministic provider rejection;
- data conflict;
- internal logic failure;
- timeout;
- partial side-effect failure.

## Retry ownership

Exactly one layer should own automatic retries for a given failure unless nested retries are intentionally budgeted.

For each retryable operation define:
- eligible errors;
- attempts;
- delay/backoff;
- total time budget;
- idempotency effect;
- final escalation.

## Continue vs stop

Continue only when downstream behavior has an explicit representation of the failed result.

Bad:
- ignore failure and emit missing fields.

Better:
- emit a typed failure item/status that downstream logic intentionally handles.

## Error workflow

Use centralized error handling for operational notification/escalation when it simplifies the system, but do not hide business-level branching that belongs in the main workflow.

## Timeouts

Set bounded timeouts for external dependencies. A workflow that can wait indefinitely has undefined operational behavior.

## Recovery

Define how an operator or automated process can:
- identify the failed logical object;
- see what side effects already occurred;
- retry safely;
- resume or reprocess;
- verify completion.
