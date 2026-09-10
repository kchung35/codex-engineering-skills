# Cleanup and failure policy

The lab harness should fail closed.

## Deployment failure

If workflow creation succeeds but validation of the returned identity fails, do not publish. Attempt to delete the newly created workflow if and only if its ID came directly from the create response and its name has the configured lab prefix.

If publication fails, attempt the same verified cleanup.

## Invocation ambiguity

Before a Webhook test, capture the current execution IDs for the ephemeral lab workflow. After invocation, identify executions whose IDs were not in that pre-invocation set.

If more than one new execution appears and the harness cannot uniquely correlate the intended run, fail as `AMBIGUOUS_EXECUTION`. Do not choose the newest execution by intuition.

## Timeouts

A timeout is a test outcome, not permission to pretend the run completed. Record the workflow ID and any visible execution IDs. This generic harness does not automatically stop a timed-out execution; surface the unresolved running/waiting state and apply a project-approved stop procedure if one exists.

## Assertion failure

An assertion failure does not trigger automatic source-workflow modification. Preserve the execution and return it to the caller/debugging case.

## Cleanup

Normal cleanup sequence:

1. re-fetch the workflow by deployment-receipt ID;
2. verify its current name still begins with the configured lab prefix and matches the deployment receipt;
3. verify its semantic workflow hash still matches the deployment receipt when a hash is present;
4. unpublish if possible;
5. delete;
6. verify a subsequent GET returns not found when practical.

If the identity check fails, refuse deletion and report manual cleanup required.

## Keep-for-inspection

Keeping a lab workflow is allowed only when the test plan says so. It should remain visibly named with the lab prefix, and external writes should stay disabled/isolated. Record the workflow ID and cleanup owner/action explicitly.
