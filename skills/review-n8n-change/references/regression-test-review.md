# Regression and test-adequacy review

## Start from changed semantics

For each material diff, identify the nearest existing behavior that could regress. Prefer tests that preserve known-good historical behavior over invented generic edge cases.

## Minimum useful matrix for behavioral changes

Select only relevant cases from:

- original required/happy-path case;
- known-good historical case adjacent to the changed path;
- original failing case for a bug fix;
- nearest boundary condition;
- null/missing-field case when optionality changed;
- zero/one/many items when cardinality changed;
- duplicate/retry case when a write/state boundary changed;
- dependency failure case when error/retry logic changed;
- alternate branch case when control flow changed.

## Bug fixes

A credible bug-fix review should answer both:

1. Does the original failing fixture now pass?
2. Does at least one representative previously successful fixture still pass?

If the root cause had multiple plausible causal paths, add tests that distinguish those paths rather than one broad end-to-end green test.

## Test oracle quality

Reject tests whose assertion only checks that the workflow returned HTTP 200 or status `success` when the requirement concerns output content or side effects.

Prefer deterministic assertions on exact fields, item counts, branch execution, destination state, or other observable invariants.

## Test isolation

Runtime evidence must come from a non-production environment or otherwise explicitly safe read-only capture. Do not recommend experimenting against production for convenience.
