# Causal Investigation Protocol

## Goal

Debugging is inference from effects to causes. A plausible explanation is not enough. Build an evidence chain that identifies the mechanism responsible for the observed instance.

## Evidence ladder

Use this as a qualitative hierarchy, not a numeric score.

### Level 0 — speculation

A mechanism is conceivable but unsupported by case-specific evidence.

### Level 1 — association

The suspect condition correlates with failures or differs from known-good executions.

### Level 2 — localization

Evidence places the first semantic divergence at or immediately after the suspect condition.

### Level 3 — mechanism

The causal path from suspect condition to failure is technically demonstrated and present in the failing case.

### Level 4 — intervention/counterfactual

Changing only the suspect causal variable changes the outcome as predicted, or a safe equivalent counterfactual comparison exists.

### Level 5 — robustness

The corrected behavior survives the original failure, known-good cases, and relevant boundary/regression tests.

A root cause should ordinarily reach Levels 3-4 before a permanent fix and Level 5 before closure. When intervention is unsafe or impossible, document why and state what alternative evidence supports the causal claim.

## Hypothesis quality

A useful hypothesis has the form:

> Condition X in component Y causes mechanism Z, which produces the exact failure signature under circumstances Q.

Bad: "Maybe the Merge node is broken."

Better: "The Merge node recombines items by a different association than the downstream expression assumes, so item 4 reads `fund_id` from the wrong upstream item whenever the two branches have unequal cardinality."

## Competing explanations

Maintain hypotheses that are causally distinct. When two hypotheses predict the same observations, design a test that separates them or mark one as subsumed if it is merely a more general version of the other.

## Contradiction protocol

When an observed result contradicts a hypothesis prediction:

1. verify the experiment itself was valid;
2. record the contradiction as evidence;
3. weaken, reject, or refine the hypothesis;
4. update the system model if the contradiction exposes a false assumption;
5. expand the hypothesis space only if existing hypotheses no longer cover the evidence.

Do not add auxiliary assumptions solely to protect a favored hypothesis.

## Multiple causes

Distinguish:

- `PRIMARY`: directly generates the failure in the observed execution.
- `CONTRIBUTING`: required or materially increases likelihood/severity but may not independently generate it.
- `LATENT_CONDITION`: pre-existing weakness that enables the primary cause.
- `AMPLIFIER`: worsens impact without creating the initial defect.
- `CONSEQUENCE`: downstream effect, not cause.

Ask of every confirmed cause:

- Is it necessary for this observed failure?
- Is it independently sufficient to recreate the signature?
- Does it require another condition?
- Could another unresolved mechanism recreate the signature without it?

Do not force binary necessary/sufficient labels when the system is probabilistic or stateful; document uncertainty.

## Closure

Causal closure is not philosophical certainty. It means the material hypothesis space generated from the system model and observed evidence has been resolved enough that the selected fix does not depend on an untested critical assumption.

A residual unknown may remain if it:

- cannot independently invalidate the fix;
- has low evidence/materiality;
- cannot safely be tested now;
- is explicitly recorded as residual risk.
