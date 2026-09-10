# Candidate binding

Use a behavioral fingerprint over workflow fields that affect execution semantics. Exclude API/read-only metadata such as timestamps, current version IDs, sharing metadata, and editor-only position where appropriate.

The release must compare the same fingerprint algorithm used by review.

## Required equalities

Before stage:

`candidate == release_plan == review_verdict`

Before publish:

`current_draft == staged_record == approved_candidate`

After publish:

`activeVersionId == staged_version_id`

## Stale review

If the candidate changes after review, even by a seemingly minor behavioral parameter, the previous review cannot certify the new candidate.

Non-behavioral editor-only changes can be ignored only if the canonical fingerprint algorithm explicitly excludes them.
