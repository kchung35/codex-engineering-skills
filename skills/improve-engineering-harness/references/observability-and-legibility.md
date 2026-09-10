# Agent observability and legibility

From the agent's perspective, inaccessible state effectively does not exist.

Make important engineering facts inspectable through stable interfaces:

- versions and environment identity;
- workflow/artifact fingerprints;
- execution IDs and status;
- structured logs/errors;
- schemas/contracts;
- database/state queries with safe permissions;
- CI/test results;
- deployment/release state;
- ownership/source-of-truth paths.

Prefer machine-readable outputs with stable field names. Avoid requiring screenshot interpretation or manual UI navigation for repeatable engineering checks when an API/CLI is available.

Observability should expose enough information to distinguish competing hypotheses, not indiscriminately dump sensitive payloads.
