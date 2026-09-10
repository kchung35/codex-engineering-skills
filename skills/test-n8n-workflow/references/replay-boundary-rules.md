# Replay boundary rules

A replay boundary is a node whose output items become the controlled input fixture for the retained downstream workflow cone.

## Valid boundary conditions

A boundary is valid when all of the following are materially true:

1. the behavior under test is downstream of the boundary;
2. captured output items contain the information downstream logic needs;
3. downstream nodes do not require removed upstream node outputs through expressions such as `$node["Upstream"]...` or `$('Upstream')...`;
4. downstream behavior does not depend on an upstream branch executing for side effects/state;
5. selected output index represents the branch being tested;
6. binary assets and item-linking semantics are either preserved or irrelevant to the test.

## Same-name replacement

The replay compiler replaces the selected boundary node with a Code node that keeps the original node `name` and `id`. This preserves common downstream references to the boundary itself.

It does not preserve:

- references to other removed upstream nodes;
- the original node's internal behavior;
- original trigger metadata;
- arbitrary paired-item ancestry beyond the replay boundary;
- binary content stored outside the fixture.

## Cross-boundary expression scan

The compiler scans retained parameters for common n8n cross-node reference forms, including `$node["Name"]`, `$node['Name']`, and `$('Name')`. If a retained node references a removed node, compilation fails by default.

The scan is intentionally conservative and cannot prove there are no dynamically constructed references. If expressions build node names dynamically or Code nodes access workflow state indirectly, inspect manually.

## Multi-output nodes

For IF, Switch, router-like, or other multi-output boundaries, replay one output index at a time. A fixture captured from output 0 does not test output 1 semantics.

If branch selection itself is under test, move the boundary upstream of the branch node.

## Paired items

n8n item linking can matter when expressions ask for an item from a previous node. A replay injector can reproduce the boundary's output data but may not reproduce the full original ancestry graph. If downstream logic relies on `.item`, paired-item metadata, or item matching to nodes before the boundary, boundary replay is not faithful enough; choose an earlier boundary or a native lab run.
