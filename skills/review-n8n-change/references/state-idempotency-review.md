# State, retries, and idempotency review

Apply whenever the candidate writes external state, persists data, waits/resumes, retries, deduplicates, or can run concurrently.

## External-write questions

For each changed write:

1. What is the logical operation identity?
2. Can the same event execute twice?
3. Can the write succeed while n8n records failure or loses the acknowledgment?
4. What happens if execution resumes/retries after that point?
5. Is the destination operation inherently idempotent, keyed, transactional, or deduplicated?
6. Is the idempotency key stable across retries and replays?

## Partial failure

Map the commit points. If A succeeds and B fails, determine whether retry re-runs A. Review compensating action only when it is actually required; idempotent replay is often simpler and safer.

## Concurrency

Check shared state for:

- read-modify-write races;
- uniqueness assumptions not enforced atomically;
- last-write-wins corruption;
- ordering dependencies;
- duplicate event processing.

Prefer evidence from database constraints or destination semantics over model claims that concurrency is "unlikely."

## Static workflow state

Changes involving workflow static data need special care because state persists across executions and may not be represented by ordinary fixture replay. Require a test strategy that actually exercises the relevant state lifecycle.
