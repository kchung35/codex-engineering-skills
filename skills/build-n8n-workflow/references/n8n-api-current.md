# Current n8n public API notes

This reference captures API details relevant to building workflow candidates. Re-verify against the target n8n version when behavior is safety-critical.

## Create workflow

The public API create-workflow request requires:
- `name`
- `nodes`
- `connections`
- `settings`

It supports `projectId` on creation.

Workflow/node response objects contain read-only fields that should be stripped from candidate request payloads.

## Update workflow

Updating a currently published workflow can republish the updated version by default.

For design/build work outside the release step, use:

`publishIfActive=false`

so a currently published workflow keeps its published version live while the new saved version remains a draft.

Do not let generic build tooling default to production publication.

## Useful settings

Current workflow settings include, among others:
- `executionTimeout`
- `errorWorkflow`
- `timezone`
- `executionOrder`
- `callerPolicy`
- `callerIds`
- execution data save/redaction settings.

`callerPolicy` supports restrictions such as same-owner, allowlist, any, or none.

## Deprecated node error flag

The workflow schema marks `continueOnFail` deprecated in favor of `onError`.

New design should use current error semantics unless compatibility with an existing older workflow requires otherwise.

## Read-only/derived values

Fields such as workflow ID/version/timestamps/active state and certain derived settings should not be treated as editable design input merely because they appear in GET responses.

Always compare against the current API schema before extending the sanitizer.
