# n8n Failure Taxonomy

Use this taxonomy to prevent anchoring. Do not create one hypothesis per category mechanically; consider only categories capable of producing the actual signature.

## 1. Input and data shape

- missing/optional/null fields
- type drift: number vs string, object vs array
- empty collections
- unexpected cardinality
- malformed or truncated input
- binary/file metadata differences
- timezone/date parsing
- upstream schema/version change

## 2. Data contract and transformation

- field renamed/dropped
- normalization inconsistency
- unit/scale mismatch
- lossy transformation
- incorrect default/fallback
- canonicalization collision
- stale contract assumption between nodes or workflows

## 3. n8n item identity and linking

- wrong item paired to previous-node data
- item count/order changes
- Code node fails to preserve lineage when needed
- expression resolves against an unintended linked item
- merge/branch recombination changes association

## 4. Expression and node configuration

- expression references wrong node/path
- optional value not guarded
- node parameter evaluated per item differently than expected
- configuration drift
- wrong operation/resource mode
- hidden default or version-dependent node behavior

## 5. Code-node implementation

- indexing/cardinality assumption
- mutation or shared-state assumption
- exception swallowed/converted
- non-deterministic iteration/order
- incorrect async behavior
- parsing/serialization bug
- numerical/string coercion
- locale/timezone dependency

## 6. Control flow

- IF/Switch predicate mismatch
- wrong branch convergence
- loop termination or batch behavior
- skipped node due to upstream empty output
- error branch unexpectedly absorbs failure
- Wait/resume behavior changes state

## 7. Sub-workflow boundary

- caller/callee contract mismatch
- workflow version mismatch
- unexpected invocation mode
- changed return structure
- duplicated or recursive invocation

## 8. Database/state

- stale state
- missing/incorrect constraint
- duplicate row
- incorrect upsert key
- transaction boundary
- race between read/write
- isolation/visibility issue
- wrong environment/database/schema
- query parameter/type mismatch

## 9. Idempotency/retry

- same logical event processed twice
- retry replays irreversible side effect
- partial failure leaves state that changes retry behavior
- generated idempotency key unstable
- retry uses changed workflow semantics

## 10. Concurrency/order

- execution interleaving
- out-of-order messages/events
- shared mutable external state
- parallel branch timing
- eventually consistent dependency
- lock/contention issue

## 11. External API/service

- changed response schema
- pagination bug
- partial response
- rate limit
- timeout
- transient 5xx/network failure
- service-specific idempotency behavior
- external state changed between calls

## 12. Authentication/authorization

- expired/revoked token
- different credential reference
- insufficient scope
- environment-specific permission
- shared credential visible/runnable but not editable

## 13. Runtime/environment/version

- n8n version difference
- node version difference
- environment variable difference
- timezone/configuration difference
- queue/worker/task-runner difference
- community/custom node mismatch
- package/runtime dependency difference

## 14. Resource/performance

- memory pressure
- execution timeout
- payload size
- binary-data storage behavior
- too many items/API calls
- database/query latency
- queue/concurrency limits

## 15. Side-effect semantics

- operation succeeds remotely but response/ack is lost
- operation is non-atomic
- duplicate create/send/write
- rollback impossible
- downstream system accepts partial payload

## 16. AI / probabilistic component

- non-deterministic model output
- prompt/schema mismatch
- parser accepts structurally valid but semantically wrong result
- model/provider/version change
- truncation/token limit
- temperature/sampling or tool-choice variability
- confidence incorrectly treated as correctness

## 17. Observability artifact

Sometimes the perceived defect is in what is observed rather than what executed:

- execution data pruned/missing
- UI shows different saved/published version than assumed
- stale cached view
- error handling hides the first failure
- logging omits the decisive field

Treat this as a real hypothesis only when it can explain the signature.
