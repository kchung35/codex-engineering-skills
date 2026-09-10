# n8n publication semantics

Current n8n uses publication/version concepts rather than treating the legacy boolean `active` field as the sole source of truth. `activeVersionId` is the key publication identity exposed by current workflow responses.

## Staging

Updating a currently published workflow can republish automatically unless `publishIfActive=false` is used. Release automation must therefore stage with `publishIfActive=false`.

## Publishing

The publication endpoint accepts an explicit `versionId`. Use it. Do not omit the version ID in an automated production release.

## Unpublishing

Current public API/CLI terminology may expose activate/deactivate aliases for publish/unpublish depending on client/version. Use the documented endpoint for the installed version and verify the resulting `activeVersionId`/published state rather than trusting naming.

## Trigger reconciliation

Publication can reconcile registered triggers. A control-plane version match is necessary but still requires runtime/operational verification for trigger-sensitive changes.
