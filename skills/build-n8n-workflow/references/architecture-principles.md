# Architecture principles

Use these as decision criteria, not rigid laws.

## 1. Make semantics visible

A future engineer or agent should be able to answer:
- what this region does;
- what data enters/leaves;
- where side effects happen;
- where state lives;
- what happens on failure.

Prefer explicit boundaries over clever cross-node coupling.

## 2. Minimize accidental coupling

Coupling is justified when two operations must share a transaction, item context, or atomic decision. It is accidental when one node depends on distant implementation details merely because an expression can reach them.

## 3. Separate transformation from effects

Pure transformations are easier to replay and test. Put database writes, sends, uploads, publishes, and mutations behind clear boundaries when practical.

## 4. Normalize early

External schemas are often unstable. Convert them to an internal canonical contract near ingestion, then make the rest of the workflow consume the canonical shape.

## 5. Design for replay

Assume an execution can be retried, duplicated, resumed, or partially replayed. Side effects must therefore have explicit duplicate semantics.

## 6. Prefer bounded complexity

A single huge workflow is hard to reason about; excessive sub-workflow fragmentation creates orchestration overhead and hidden contracts. Split only at stable semantic boundaries.

## 7. Optimize for operational legibility

Node names, notes, contracts, correlation IDs, and predictable failure paths matter more than visual compactness.

## 8. Keep production behavior stable

An intentional feature change is not permission to rewrite unrelated regions. Prefer local architecture evolution unless the current structure blocks correctness or materially increases risk.

## 9. Put invariants in mechanisms

When possible, enforce critical rules with database constraints, validation nodes, deterministic scripts, unique keys, or API permissions rather than prose alone.

## 10. Treat observability as architecture

If future failure reconstruction would require guessing, the design is incomplete.
