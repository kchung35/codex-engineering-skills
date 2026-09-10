# Integration and security review

Apply to changed external I/O, credentials, HTTP/database operations, webhooks, Code nodes, filesystem/command nodes, caller policies, and MCP exposure.

## Integration contract

Check:

- request method/path/query/body construction;
- pagination and continuation semantics;
- status-code handling;
- timeout/retry ownership;
- response schema/null handling;
- rate-limit behavior;
- authentication/authorization assumptions;
- test-vs-production endpoint separation.

## Credentials

Workflow JSON should contain credential references, not plaintext secrets. A changed credential reference is a material integration change even if node parameters are otherwise identical.

Do not request or expose credential values merely to review a workflow.

## Dynamic destinations and queries

Pay special attention to:

- externally supplied URLs/hosts;
- dynamic SQL/query expressions;
- shell/command execution;
- filesystem access;
- arbitrary Code-node network behavior where applicable.

Static scanners can flag these surfaces but cannot prove them safe. Inspect the effective operation.

## Webhooks and callable workflows

Review authentication, path exposure, allowed callers, replay/duplicate handling, and whether new public/MCP reachability is intended.

## n8n security audit

Where the deployment supports it and a broader instance audit is explicitly in scope, n8n exposes a security audit covering credentials, database query-expression usage, filesystem nodes, risky/community/custom nodes, and instance-level issues. This review skill does not run instance mutations or expand scope automatically.
