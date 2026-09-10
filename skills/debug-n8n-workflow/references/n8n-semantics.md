# n8n Semantics Checklist

Use this reference when the defect may depend on n8n behavior rather than only ordinary code logic.

Official documentation changes over time; verify current behavior against the installed n8n version and current n8n docs when a semantic detail is decisive.

## Item model and lineage

Check:

- number of input and output items at each relevant node;
- whether a node changes cardinality or ordering;
- whether downstream expressions rely on previous-node item association;
- whether custom/programmatic output preserves item lineage when required;
- whether a Code node returns the expected item structure;
- whether the first wrong value is caused by wrong content or wrong item association.

n8n uses item-linking information to resolve data from preceding items. Missing/incorrect lineage can make downstream references resolve incorrectly, especially when item cardinality changes.

Current docs: https://docs.n8n.io/data/data-mapping/data-item-linking/

## Expressions and cross-node references

Inspect every material expression for:

- source node and path;
- behavior with missing/null values;
- item-specific vs aggregate assumptions;
- references across branches;
- renamed nodes/fields;
- saved/published workflow differences;
- whether the expression is evaluated in the context assumed by the author.

Current docs: https://docs.n8n.io/data/data-mapping/data-mapping-ui/

## Merge, branches, and loops

When paths split or converge, explicitly model:

- branch predicates;
- cardinality on each branch;
- merge mode and matching assumption;
- execution order if relevant;
- loop/batch boundaries;
- empty-output behavior;
- downstream assumptions after recombination.

Do not infer semantics from node names alone; inspect actual configuration and installed node version.

## Code nodes

Inspect:

- execution mode;
- exact input/output structure;
- array indexing and cardinality assumptions;
- preservation of lineage when output items are constructed manually;
- exception handling;
- mutation/shared state assumptions;
- date/time/locale behavior;
- non-determinism;
- dependencies/features available in the deployed runtime.

## Workflow/execution versions

Distinguish among:

- workflow state at the original failing execution;
- currently saved workflow;
- currently published/active workflow;
- cloned/debug workflow.

A retry with the current workflow tests a different question from replaying the original workflow state.

Current execution docs: https://docs.n8n.io/workflows/executions/all-executions/

## Credentials

Treat credential identity, scope, and availability as configuration evidence. Never export secret values merely to compare environments.

A workflow can sometimes be runnable by an editor even where credential editing is restricted, so "it runs" and "the credential is available/editable" are different questions.

Current sharing docs: https://docs.n8n.io/workflows/sharing/

## Environment

When local and hosted behavior differ, capture:

- n8n version;
- node versions;
- execution mode/queue/task-runner differences;
- timezone;
- relevant environment variables;
- custom/community nodes;
- external dependency versions/endpoints;
- concurrency/resource limits.
