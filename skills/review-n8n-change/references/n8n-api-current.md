# Current n8n API facts relevant to review

This reference captures API semantics that matter to release-readiness checks. Treat the live installed version as authoritative when it differs.

## Workflow identity

Current workflow responses expose a current `versionId`; published workflows can also expose an active version identifier. Preserve these identifiers in snapshots when they help distinguish what was saved, tested, or published.

## Workflow updates

Current public API semantics support updating a workflow as a draft with `publishIfActive=false`. Without draft-preserving behavior, an update to a currently published workflow can republish the new version when permissions allow.

The review skill must not call workflow update/publish operations. This fact matters when assessing whether upstream build/test tooling could have changed the live workflow.

## Execution evidence

Execution retrieval can include detailed run data and the saved workflow data associated with the execution. It also exposes workflow version identity and indicators for redacted or oversized execution data.

Treat redacted/truncated data as insufficient when the review depends on fields that are unavailable.

## Execution retry

Retry can run previous execution data against the currently saved workflow. This can be useful in a non-production lab but means the reviewer must bind the resulting evidence to the exact reviewed candidate rather than assuming a retry proves a particular version.
