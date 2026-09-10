# Post-release verification

Verification should be proportional to blast radius and side-effect risk.

## Control plane

Always verify the exact published version.

## Runtime evidence

Prefer, in order:

1. passive real executions that naturally occur soon enough;
2. a safe synthetic canary whose side effects are isolated or idempotent;
3. an explicitly bounded production smoke action;
4. control-plane-only verification when runtime verification is not safely possible.

Control-plane-only verification is weaker evidence and must be represented as such.

## Version binding

When n8n execution metadata exposes `workflowVersionId`, require it to match the published candidate for evidence used as release proof.

## Regression indicators

Define them before publication where possible: error rate, expected output invariant, downstream write count, retry count, trigger success, latency bound, or domain-specific correctness evidence.
