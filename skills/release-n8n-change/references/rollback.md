# Rollback

Rollback should restore the known prior runtime state, not invent a new state under pressure.

## Previously published workflow

Preferred rollback target:

`original activeVersionId`

Publish that historical version explicitly and verify it becomes active again.

## Previously unpublished workflow

Rollback by unpublishing the newly published workflow and verify it is no longer published.

## Draft state

Publishing the prior version does not necessarily restore the pre-release draft. That is acceptable. Runtime restoration has priority.

Do not overwrite the draft automatically unless the release plan explicitly requires it and the restored draft content is bound/validated.

## Rollback failure

If the rollback request fails or the expected prior publication state cannot be confirmed, stop all further mutation and escalate as `ROLLBACK_UNCONFIRMED`.
