# Documentation and AGENTS discipline

Treat repository knowledge as a system of record, not a prompt dump.

## AGENTS.md

Use it as a short map containing:

- system purpose;
- high-level architecture/doc pointers;
- environment/source-of-truth map;
- safety invariants;
- validation commands;
- Skill routing;
- where durable case artifacts live.

Do not copy detailed API contracts, long taxonomies, tutorials, or volatile facts into AGENTS.md.

## Structured docs

Give durable subjects stable paths and owners. Prefer indices and cross-links over duplicated paragraphs.

## Generated truth

When a fact can be generated from code/schema/config, consider generating the documentation or validation rather than maintaining prose manually.

## Deletion is improvement

When adding guidance, remove superseded or duplicated rules. Smaller, more authoritative context is often better than additive context.
