# Fixture contract

Fixtures are portable boundary-output items used by `BOUNDARY_REPLAY`.

## Schema

```json
{
  "schema_version": 1,
  "metadata": {
    "fixture_id": "CASE-123-failing-01",
    "boundary_node": "Parse Document",
    "output_index": 0,
    "provenance": {
      "kind": "historical_execution",
      "source_execution_id": "81234",
      "note": "original failing execution"
    },
    "sha256": "computed-over-items"
  },
  "items": [
    {"json": {"document_id": "DOC-1", "value": 42}}
  ]
}
```

`items` must be a JSON array. Each entry must contain a `json` object. Optional item fields are preserved only when explicitly supported by the harness.

## Provenance kinds

Recommended values:

- `historical_execution`
- `known_good_execution`
- `synthetic`
- `boundary_capture`
- `minimized_reproducer`

For historical fixtures, include the source execution ID where policy permits.

## Digest

The SHA-256 digest is computed over a canonical JSON serialization of `items`, not over the metadata envelope. Changing fixture items therefore changes the digest while notes/provenance may evolve independently.

## Historical fixture immutability

Do not edit a historical fixture's `items` and keep the old identity. Create a new fixture with a new ID and provenance note.

## Sensitive data

A fixture can contain real execution data. Store it only where project policy permits and keep generated artifacts out of Git by default. Prefer a minimized fixture when the sensitive fields are irrelevant to the mechanism.

## Binary data

Execution JSON can contain `binary` metadata without containing the actual underlying binary bytes. Those references may point to instance-local filesystem/object storage and are not portable to another n8n instance.

The default validator rejects fixtures containing `binary`. Use native-trigger testing, provision a lab binary asset explicitly, or extend the harness with a project-approved binary transport mechanism.
