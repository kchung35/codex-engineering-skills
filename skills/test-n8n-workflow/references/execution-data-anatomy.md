# n8n execution data anatomy

The harness relies on n8n's public execution API rather than scraping the editor UI.

At the time this skill was authored, execution responses include fields such as:

- `id`
- `mode`
- `retryOf`
- `status`
- `startedAt`
- `stoppedAt`
- `workflowId`
- `workflowVersionId`
- `storedAt`
- `jsonSizeBytes`
- detailed `data` when requested
- `workflowData` when detailed data is requested
- `dataTooLargeToDisplay` when configured display limits suppress the detail

The common detailed run structure used by assertions is:

`data.resultData.runData.<nodeName>[runIndex].data.main[outputIndex][itemIndex]`

Node runs may contain `error` instead of or in addition to output data.

## Redaction

The public API supports an execution-data redaction control. The harness does not request revealed data by default. If the lab workflow's policy redacts the information required by a test, treat the result as insufficient evidence rather than interpreting redacted/missing data as an application failure.

Explicit reveal requires appropriate n8n scope and local opt-in. Only use it when policy allows the underlying data to be inspected.

## Oversized executions

The API can omit detailed data when it exceeds the configured display-size limit and mark the response accordingly. The harness should surface this state. Do not automatically request unlimited data for every run; use the override only when the test requires it and local policy permits the storage/transfer.

## Version identity

Record `workflowVersionId` whenever present. Comparing two executions without checking which workflow version ran can produce a misleading conclusion.

## Execution modes

Common modes include manual, retry, trigger, webhook, evaluation, chat, and agent. The harness usually expects `webhook` for boundary replay and `retry` for explicit retry testing. An unexpected mode is evidence worth reporting.
