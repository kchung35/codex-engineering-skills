# Observability

Design so an execution can be reconstructed without reading a person's memory.

## Correlation

Carry stable identifiers from ingress through side-effect boundaries. Useful dimensions include:
- business object/document/package ID;
- source event/message ID;
- n8n execution ID;
- idempotency key;
- processing version;
- external request/result ID.

## Structured status

Prefer machine-readable stage/status/error categories to prose-only logs.

Useful fields:
- stage;
- status;
- attempt;
- started_at;
- completed_at;
- error_class;
- provider_status;
- entity_id;
- execution_id.

## Evidence boundaries

After a critical side effect, capture enough non-secret evidence to prove what happened:
- affected record ID;
- provider message ID;
- row count;
- returned version/etag;
- canonical output digest.

## Custom execution data

When supported by the target n8n plan, execution custom data can make executions filterable by business identifiers. Use it for high-value correlation, not arbitrary payload logging.

## Sensitive data

Do not log credentials, tokens, or full sensitive payloads unless explicitly required and approved. Prefer hashes, IDs, counts, and selected safe fields.

## Debuggability test

Ask:
> If this execution fails three months from now, what facts will an engineer need to identify the logical object, first failed boundary, prior side effects, and safe recovery action?

If those facts are unavailable, improve the design.
