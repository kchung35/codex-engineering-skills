# Lab safety model

The live harness is permitted to mutate only an explicitly declared non-production n8n environment. Textual intent such as "this is just testing" is not enough; the scripts require a machine-readable lab configuration and an API key supplied through the environment.

## Lab configuration

Recommended `lab-config.json`:

```json
{
  "schema_version": 1,
  "environment_class": "NON_PRODUCTION",
  "instance_base_url": "https://acme-lab.app.n8n.cloud",
  "webhook_base_url": "https://acme-lab.app.n8n.cloud",
  "project_id": "P123",
  "workflow_name_prefix": "LAB__",
  "credential_reference_policy": "REQUIRE_MAP",
  "allowed_test_targets": ["lab-postgres", "mock-api"],
  "allow_external_writes": false,
  "max_fixture_bytes": 1048576,
  "max_cases_per_matrix": 25,
  "max_run_seconds": 180,
  "poll_interval_seconds": 1.5,
  "production_deny_hosts": ["n8n.acme.com", "n8n-prod.acme.com"],
  "external_deny_hosts": ["api.acme.com", "db-prod.acme.com"],
  "node_type_versions": {"webhook": 2.1, "code": 2}
}
```

Required invariants:

- `environment_class` must equal `NON_PRODUCTION` exactly.
- `instance_base_url` must use HTTPS except for explicit localhost development.
- neither the API instance hostname nor the Webhook hostname may match any `production_deny_hosts` entry;
- static HTTP destinations matching `external_deny_hosts` are rejected by the workflow safety gate;
- `allowed_test_targets` is the explicit alias allowlist used by `TEST_TARGET` classifications;
- `workflow_name_prefix` must be non-empty and should visibly identify ephemeral lab workflows;
- the API key is read from `N8N_LAB_API_KEY`; never persist it in JSON, shell history examples, Git, logs, or execution artifacts;
- bounds must be positive and conservative.

`webhook_base_url` is separate from `instance_base_url` because reverse proxies and self-hosted n8n can expose Webhooks through a different public base URL. Do not infer it when the deployment topology says otherwise.

## Side-effect manifest

Unknown/external nodes default to `DENY`.

Example:

```json
{
  "schema_version": 1,
  "default": "DENY",
  "nodes": {
    "Fetch Portfolio": {
      "classification": "READ_ONLY",
      "reason": "HTTP GET against lab API"
    },
    "Write Result": {
      "classification": "TEST_TARGET",
      "target": "lab-postgres",
      "reason": "writes only to disposable lab table"
    },
    "Send Email": {
      "classification": "STUBBED",
      "reason": "replaced by capture node in lab"
    }
  }
}
```

Classifications:

- `LOCAL`: pure local/control-flow computation with no external mutation.
- `READ_ONLY`: external dependency is contacted but operation is demonstrably non-mutating.
- `TEST_TARGET`: mutation goes only to a disposable or explicitly isolated test system/account/table/bucket/mailbox. The manifest entry must include a `target` alias present in `allowed_test_targets`.
- `STUBBED`: original side effect has been replaced with a local/test double.
- `WRITE_ALLOWED`: a real external mutation is intentional. This is exceptional and requires both `allow_external_writes: true` in the lab config and an explicit CLI acknowledgment.
- `DENY`: must not execute.

Do not classify by node display name. Inspect node type, operation, HTTP method, SQL statement, destination, credential reference, and relevant expressions. A non-local node may not be labeled `LOCAL` to bypass the manifest gate.

## Pure/local node allowlist

The validator has a deliberately small allowlist for common local n8n nodes. Everything else needs an explicit manifest entry. False positives are acceptable; false negatives are not.

An n8n node can still become unsafe through its parameters. For example, a Code node can theoretically make network calls in environments that enable external modules. Treat the allowlist as a baseline, not proof against deliberately hostile code. If Code-node source imports modules, uses environment secrets, shells out, or performs external I/O, classify it explicitly and inspect it.

## Credential rules

The harness never uses n8n credential export APIs and never accepts plaintext secret material. A workflow may contain credential references. In `REQUIRE_MAP` mode, every retained reference must be mapped to a credential already provisioned in the lab. In `REUSE_REFERENCES` mode, retained references may be reused only when the configured lab is the same non-production instance/project where those references are known to be valid.

## Production containment

The scripts protect against accidental targeting, not malicious configuration. The strongest control is infrastructure-level separation: a dedicated development/test n8n instance with least-privilege API keys and test-only credentials. Textual guardrails are a secondary layer.
