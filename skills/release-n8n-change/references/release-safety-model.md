# Release safety model

A release is not a design session. The release controller should have less discretion than the builder, debugger, or reviewer.

## Safety properties

A safe release should establish five bindings:

1. **Intent binding** — this workflow ID is the intended production object.
2. **Candidate binding** — the bytes/behavioral content being staged are the reviewed candidate.
3. **Source binding** — production has not drifted since the change was prepared/reviewed.
4. **Publication binding** — the exact staged version, not an unspecified latest draft, becomes active.
5. **Evidence binding** — post-release observations correspond to the published candidate.

If any binding is ambiguous, stop.

## Separate control plane from data plane

Control-plane success means the intended version is published.

Data-plane success means executions behave correctly.

A publication API returning 200 proves neither the complete trigger state nor business correctness by itself.

## One workflow by default

Atomic multi-workflow releases are not generally available through ordinary n8n workflow operations. Treat each workflow as a separately bound release object. If a feature spans workflows, declare ordering/dependencies and rollback order explicitly.

## Production mutation switch

Scripts should require both:

- a configuration value explicitly allowing production mutation; and
- an independent command-line confirmation flag.

This prevents a checked-in config or copied command from being sufficient on its own.
