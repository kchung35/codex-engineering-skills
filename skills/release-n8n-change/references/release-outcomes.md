# Release outcomes

Use precise terminal outcomes.

## RELEASED_VERIFIED

Exact candidate version is live and required control-plane/runtime verification passed.

## RELEASED_LIMITED_VERIFICATION

Exact candidate version is live, but the approved verification strategy could not safely prove all runtime behavior. Residual uncertainty is documented.

## ROLLED_BACK_VERIFIED

Release was attempted, rollback criteria were met, and the prior runtime publication state was restored and verified.

## STOPPED_BEFORE_PUBLICATION

A binding, drift, permission, staging, or safety gate failed before intended publication.

## ROLLBACK_UNCONFIRMED

Rollback was attempted or required but the prior runtime state could not be confirmed. Treat as incident state.
