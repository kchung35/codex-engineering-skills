# Codex Engineering Skills

A collection of reusable Codex engineering skills and supporting resources.

## Skills

- `debug-n8n-workflow` — evidence-driven forensic debugging for complex n8n workflows, with causal hypothesis management, controlled experiments, root-cause closure, minimal-fix selection, and verification gates.
- `test-n8n-workflow` — deterministic non-production n8n laboratory harness for boundary-fixture replay, side-effect gating, credential-reference remapping, hosted execution capture, semantic assertions/diffs, regression matrices, and verified cleanup.
- `build-n8n-workflow` — requirements-to-candidate engineering workflow for new features and intentional n8n changes, with explicit contracts, state/idempotency, failure semantics, observability, scoped architecture decisions, static validation, and test handoff.

## Repository layout

```text
skills/
  debug-n8n-workflow/
    SKILL.md
    agents/
    references/
    scripts/
  test-n8n-workflow/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
  build-n8n-workflow/
    SKILL.md
    agents/
    assets/
    references/
    scripts/
```

Keep company-specific credentials, workflow exports, internal URLs, schemas, and proprietary data out of this repository unless the repository is explicitly approved for that material.
