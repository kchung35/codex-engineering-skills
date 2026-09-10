# Credential remapping

The harness handles credential references only. It never exports or transports credential secret values.

## REQUIRE_MAP

Recommended when the lab is a different instance or project.

Example `credential-map.json`:

```json
{
  "schema_version": 1,
  "credentials": {
    "source-credential-id": {"id": "lab-credential-id", "name": "Lab API"},
    "Production DB": {"id": "lab-db-id", "name": "Lab DB"}
  }
}
```

Keys may match the source reference's `id` or `name`. Values must contain only lab credential reference metadata. No tokens, passwords, client secrets, private keys, or connection strings.

If any retained credential reference cannot be mapped, clone compilation fails.

## REUSE_REFERENCES

Allowed only when the configured target is an explicitly non-production environment where the original reference is known to be valid and appropriate for testing.

Do not use this mode merely to avoid provisioning test credentials.

## Semantic compatibility

A successful remap proves only that a reference exists in the workflow payload. It does not prove that the lab credential points to the correct test account/system or has the same permissions as production. Record those differences in the test plan when they affect the mechanism.

## Credential-dependent failures

When authentication/authorization itself is under test, use `NATIVE_TRIGGER_LAB` with a deliberately provisioned test credential. A downstream replay that bypasses the credentialed node cannot verify credential behavior.
