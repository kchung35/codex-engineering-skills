# Production drift detection

Production drift is any change to the release source state that was not incorporated into the reviewed change.

Check at least:

- behavioral workflow fingerprint;
- workflow ID;
- current draft version ID;
- published `activeVersionId`;
- relevant runtime settings.

Capture baseline immediately before stage, not hours earlier.

Recheck immediately before stage and again before publish. This narrows the race window but does not make the API transactional.

Never auto-merge workflow JSON drift in the release skill. Return to build/review.
