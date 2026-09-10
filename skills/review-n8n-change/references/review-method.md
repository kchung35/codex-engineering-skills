# Independent review method

## Purpose

Review the candidate as a verifier whose job is to discover unsupported assumptions and material regressions, not to defend the implementation.

## Evidence order

Use this order whenever practical:

1. requirements and invariants;
2. source workflow behavior relevant to the change;
3. candidate workflow;
4. deterministic diff and risk outputs;
5. runtime test evidence;
6. author rationale and design notes.

This order reduces anchoring. If the rationale is already known from the conversation, reconstruct the requirement and failure surface independently before evaluating the rationale.

## Review the delta, not everything equally

Start from the semantic diff. Expand outward only as needed to understand:

- upstream contracts feeding changed nodes;
- downstream consumers affected by changed outputs/control flow;
- external systems touched by changed behavior;
- shared state or sub-workflows that create non-local consequences.

Do not turn a bounded change into a general code-quality audit.

## Defect vs preference

A finding should be tied to at least one of:

- violated requirement;
- violated invariant;
- credible correctness failure;
- data loss/corruption/duplication risk;
- security or permission regression;
- operational failure that materially prevents detection/recovery;
- compatibility break;
- demonstrated performance/scaling failure within expected operating bounds.

Do not block release because another design is aesthetically cleaner.

## Counterexample discipline

Prefer realistic counterexamples that discriminate whether the candidate satisfies its contract. A useful attack changes one meaningful assumption at a time and predicts the resulting behavior.

Avoid exhaustive lists of implausible edge cases. Stop when the material risk surface is covered and new cases add little information.

## Pre-existing defects

If a problem exists identically in source and candidate and the change neither depends on nor worsens it, record it separately as a legacy observation rather than a blocking regression.

If the candidate increases exposure to the legacy defect, changes its severity, or relies on the broken behavior, it becomes relevant to the review.
