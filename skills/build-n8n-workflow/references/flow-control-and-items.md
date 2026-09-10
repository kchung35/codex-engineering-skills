# Flow control and n8n item semantics

n8n workflows operate on items. Control-flow design must preserve the intended relationship between items.

## Itemwise vs aggregate

Choose deliberately:
- itemwise: each input item independently progresses;
- aggregate: several items become one collection for a global operation.

Document where cardinality changes.

## Branches

Each branch should represent a meaningful predicate. Define whether branches are mutually exclusive or can both execute.

Avoid duplicating the same business logic in multiple branches.

## Merge

Before adding a Merge node, state:
- what identifies matching items;
- expected cardinality on each side;
- behavior when one side is missing;
- ordering assumptions.

Do not use Merge merely to visually reunite branches if data semantics do not require it.

## Loops and pagination

Define:
- termination condition;
- page/batch size;
- maximum/bounds;
- rate-limit behavior;
- partial progress;
- retry behavior.

## Cross-node references

Prefer current-item data when practical. Long-range references can create hidden dependencies and item-linking ambiguity, especially across branches or after cardinality changes.

Every explicit `$('Node')` or `$node[...]` reference should refer to an existing node and have a reason when it bypasses the immediate data path.

## Code nodes

When programmatic logic maps output items to input items, preserve paired-item semantics where required. When aggregating or splitting, make the new mapping explicit.

## Sub-nodes

Some n8n sub-nodes resolve expressions differently from ordinary root nodes. Verify actual node semantics when multi-item behavior matters; do not extrapolate from a visually similar node.
