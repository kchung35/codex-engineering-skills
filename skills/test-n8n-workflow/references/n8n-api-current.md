# n8n public API contract used by this harness

Verified against current n8n public API source/docs on 2026-09-10. Treat this file as a compatibility snapshot, not a promise that future n8n versions will never change.

Base API URL:

- n8n Cloud: `https://<instance>.app.n8n.cloud/api/v1`
- self-hosted: `https://<domain>/api/v1`

Authentication header:

`X-N8N-API-KEY: <api key>`

## Workflow operations used

- `GET /workflows/{id}` — retrieve a workflow; requires `workflow:read`.
- `POST /workflows` — create a workflow; requires `workflow:create`.
- `POST /workflows/{id}/publish` — publish a workflow; scope is `workflow:activate` in the current API.
- `POST /workflows/{id}/unpublish` — unpublish a workflow; corresponding workflow deactivation scope.
- `DELETE /workflows/{id}` — delete a workflow; requires `workflow:delete`.

Current workflow update behavior is important even though the main lab flow avoids updating an existing target: updating a published workflow can automatically republish unless `publishIfActive=false` is supplied. Do not use generic PUT updates on a production workflow while testing.

Workflow creation currently accepts `projectId`, allowing an ephemeral workflow to be created in a designated lab project.

## Execution operations used

- `GET /executions` — list executions; requires `execution:list`.
- `GET /executions/{id}` — retrieve an execution; requires `execution:read`.
- `POST /executions/{id}/retry` — retry an execution; requires `execution:retry`.

List-execution filters currently include `workflowId`, `projectId`, `status`, `startedAfter`, and `startedBefore`, plus pagination.

`GET /executions/{id}` supports `includeData=true`. It also supports controls for oversized data and redaction. Requesting explicitly revealed data requires `execution:reveal`.

Retry accepts `loadWorkflow`:

- false/omitted: retry using the workflow stored with the original execution;
- true: retry using the currently saved workflow.

The response identifies the new retry execution ID.

## Webhook execution

n8n Webhook nodes expose separate test and production URLs. The test URL is registered while the editor is in a listen/test state; the production URL is registered when the workflow is published. This harness therefore publishes only an ephemeral workflow on the dedicated lab and invokes its production Webhook URL.

## Compatibility rule

On HTTP 404/405/409/415 or schema mismatch, do not guess a replacement endpoint and continue mutating. Stop, capture the response metadata, inspect the target n8n version/API documentation, and update this compatibility layer deliberately.
