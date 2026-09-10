# Security and privacy

Harness improvement artifacts often aggregate incidents, logs, workflows, and prompts. Treat them as potentially sensitive.

Rules:

- minimize real production payloads;
- redact secrets and credential values;
- use IDs/references rather than plaintext tokens;
- prefer synthetic minimized reproductions;
- do not publish internal URLs, proprietary schemas, manager/customer data, or organization-specific workflow exports in a public skills repository;
- keep security gate changes fail-closed;
- never weaken authorization because it creates friction;
- evaluate false blocks separately from security bypasses.

A public generic Skill may describe safe patterns without containing company-specific evidence.
