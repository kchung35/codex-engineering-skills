# Harness failure taxonomy

Use one primary class plus optional contributing classes.

## ROUTING_AMBIGUITY
A task maps to the wrong Skill or multiple Skills claim it. Typical remedy: descriptions, routing map, ownership boundaries, or merge.

## CONTEXT_DISCOVERY
Correct information exists but is not discoverable at the decision point. Typical remedy: short AGENTS map, indices, stable paths, or tooling that fetches the source.

## KNOWLEDGE_STALENESS
Repository guidance no longer matches runtime/API/system behavior. Typical remedy: source-of-truth ownership, freshness check, generated docs, or deletion of obsolete prose.

## MISSING_INVARIANT
An always-applicable rule is missing or not enforced. Prefer a mechanical invariant when possible; use AGENTS for concise repository-wide rules.

## DETERMINISTIC_REASONING_GAP
The model repeatedly performs a repeatable calculation/inspection inconsistently. Prefer a script/checker with stable output and exit codes.

## TOOL_CAPABILITY_GAP
Required action or inspection cannot be performed with available tools. Add/repair a tool or expose an API rather than prompting around the absence.

## ENVIRONMENT_LEGIBILITY
Logs, versions, state, schemas, execution traces, or runtime behavior are opaque. Improve observability or provide agent-readable inspection commands.

## FEEDBACK_LOOP_GAP
Failure is detected too late or never returns to the agent. Add tests, CI, structured review, execution evidence, or faster local checks.

## TEST_COVERAGE_GAP
A missing representative fixture/assertion allows regression or false confidence.

## EVIDENCE_BINDING_GAP
Evidence is not tied to the exact artifact/version/configuration it claims to validate. Add fingerprints/version IDs and reject stale evidence.

## SAFETY_ENFORCEMENT_GAP
A critical safety boundary relies on agent discretion or prose. Add a fail-closed gate and explicit authorization.

## SKILL_SCOPE_GAP
An existing Skill lacks a procedure that clearly belongs to its current intent. Update that Skill before creating another.

## SKILL_OVERLAP
Two Skills have substantially overlapping intent and procedure. Narrow, merge, or move common deterministic logic to shared tooling.

## MODEL_INTERFACE_GAP
Inputs/outputs are too unstructured or ambiguous for reliable reasoning. Introduce schemas, stable machine-readable results, IDs, and explicit status enums.

## PROCESS_GAP
The handoff/order among existing capabilities is unclear. Fix routing/lifecycle rather than creating a new capability by default.
