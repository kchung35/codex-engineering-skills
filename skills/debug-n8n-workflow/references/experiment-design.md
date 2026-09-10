# Diagnostic Experiment Design

## Objective

Choose experiments that reduce uncertainty about the causal model with the least risk, cost, and disturbance.

Do not simply test the highest-ranked hypothesis first if another test can discriminate several important hypotheses at once.

## Preferred order

1. Existing evidence inspection.
2. Failing vs known-good differential comparison.
3. Static graph/config/code inspection.
4. Replay of an existing failing fixture without mutation.
5. Controlled substitution of one input/config/dependency.
6. Isolated subgraph or cloned-workflow experiment.
7. Fault injection or timing/concurrency experiment.
8. Production mutation only under the repository's explicit release/incident procedure.

## Experiment template

Before execution answer:

- Which hypotheses does this test?
- What exact observation would strengthen each hypothesis?
- What exact observation would weaken/falsify it?
- What variables are held constant?
- Could the test itself alter the state that matters?
- What external side effects can occur?
- Can one cheaper observation answer the same question?

## High-information patterns

### Differential debugging

Compare the nearest known-good execution to the failing execution and locate the earliest semantic divergence, not every syntactic difference.

### Path bisection

When the relevant path is long, inspect intermediate boundaries to halve the search space.

### Fixture minimization

Remove irrelevant input dimensions while preserving the failure. A smaller reproducer often reveals the causal condition and makes later regression testing durable.

### One-variable substitution

Substitute only the suspected field/configuration/dependency. Avoid changing multiple nodes and then attributing success to one change.

### Dependency substitution

Replace an external dependency with a controlled response to distinguish workflow logic from integration behavior.

### Repeated trials

For intermittent failures, run enough repetitions under controlled conditions to distinguish deterministic data-shape bugs from timing/concurrency/probabilistic behavior. Record run count and outcomes.

## Avoid

- random patching;
- changing multiple variables simultaneously without necessity;
- testing only the happy path;
- relying on final status when intermediate semantics matter;
- using synthetic fixtures when the real failing input is available and safe;
- performing mutating diagnostics against production side effects when a clone can answer the question.
