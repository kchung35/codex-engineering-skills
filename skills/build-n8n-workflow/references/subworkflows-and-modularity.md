# Sub-workflows and modularity

A sub-workflow is a semantic module, not a visual-cleanup device.

Use one when at least one of these is strong:
- the logic is reused by multiple callers;
- it has a stable input/output contract;
- it has distinct ownership;
- it isolates an external integration or failure domain;
- it is independently testable and operationally meaningful;
- changing it independently reduces risk.

Avoid extraction when:
- the boundary would expose many internal fields;
- every caller needs different behavior;
- the sub-workflow would be a two-node wrapper with no semantic value;
- it forces more long-range state/credential coupling;
- it obscures transactionality that belongs in one workflow.

## Contract

Define the sub-workflow like an API:
- accepted input shape/cardinality;
- output shape/cardinality;
- error behavior;
- retry/idempotency expectations;
- caller permissions/policy.

Current n8n workflow settings support caller policies controlling which workflows may call a workflow. Use the narrowest policy compatible with the intended reuse.

## Versioning

If multiple workflows depend on a shared sub-workflow, treat breaking output/schema changes as migrations. Do not silently alter the contract for all callers.
