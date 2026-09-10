# Case Ledger Contract

Use the case ledger as durable investigation state. It is an engineering record, not a narrative diary.

## Directory

```
.agent-cases/<case-id>/
  case.json
  observations.jsonl
  system_model.json
  hypotheses.json
  experiments.jsonl
  causal_set.json
  fix.json
  verification.json
  closeout.md
  artifacts/
```

`artifacts/` stores snapshots, minimized fixtures, execution exports, diffs, or generated diagnostic files. Never store plaintext secrets.

## Stable IDs

Use stable identifiers so conclusions can cite evidence without repeating large payloads:

- `O001` observation
- `H001` hypothesis
- `E001` experiment
- `C001` confirmed/contributing cause
- `T001` verification test

Never silently edit a historical observation to make it fit a later conclusion. Add a correcting observation.

## case.json

Minimum shape:

```json
{
  "case_id": "CASE-20260910-221500",
  "title": "Short problem",
  "status": "OPEN",
  "stage": "BASELINE",
  "created_at": "ISO-8601",
  "environment": {
    "target": "unknown",
    "n8n_instance": null,
    "workflow_id": null,
    "workflow_name": null,
    "execution_ids": []
  },
  "failure_signature": {
    "observed": "",
    "expected": "",
    "impact": "",
    "reproduction": "unknown"
  },
  "constraints": [],
  "assumptions": [],
  "containment": []
}
```

## observations.jsonl

Append-only, one JSON object per line:

```json
{"id":"O001","timestamp":"...","kind":"DIRECT_EXECUTION","claim":"Node X output item 4 lacks fund_id","source":"execution:123/node:X/item:4","epistemic":"OBSERVED"}
```

Recommended `kind` values:

- `USER_REPORT`
- `WORKFLOW_SNAPSHOT`
- `DIRECT_EXECUTION`
- `KNOWN_GOOD_EXECUTION`
- `CODE_INSPECTION`
- `CONFIG_INSPECTION`
- `DATABASE_QUERY`
- `API_RESPONSE`
- `DIFF`
- `DOCUMENTATION`
- `CONTROLLED_EXPERIMENT`

`epistemic` should be `OBSERVED`, `TESTED`, `INFERRED`, or `ASSUMED`.

## system_model.json

Minimum useful shape:

```json
{
  "scope": {
    "entry_boundary": [],
    "impact_boundary": [],
    "relevant_nodes": []
  },
  "edges": [],
  "data_contracts": [],
  "cross_node_references": [],
  "subworkflows": [],
  "state_stores": [],
  "external_dependencies": [],
  "credential_references": [],
  "side_effects": [],
  "retry_idempotency": [],
  "timing_concurrency": [],
  "versions_settings": [],
  "first_divergence_candidate": null,
  "unknowns": []
}
```

## hypotheses.json

```json
{
  "hypotheses": [
    {
      "id": "H001",
      "class": "DATA_CONTRACT",
      "mechanism": "Upstream parser omits field X for input shape Y, causing downstream expression Z to resolve null.",
      "components": ["Parser", "Normalize"],
      "explains_signature": "...",
      "rank": "HIGH",
      "material": true,
      "evidence_for": ["O003"],
      "evidence_against": [],
      "predictions_if_true": ["..."],
      "predictions_if_false": ["..."],
      "best_test": "E002",
      "status": "ACTIVE",
      "notes": ""
    }
  ]
}
```

Do not use `CONFIRMED_CAUSE` because a patch happened to make the symptom disappear. Link confirmation to evidence.

## experiments.jsonl

Append an experiment plan before execution and then append/update a result record with the same ID.

Plan:

```json
{"id":"E001","phase":"PLAN","hypotheses":["H001","H003"],"method":"Compare failing and known-good input at Parser boundary","controlled_variables":["workflow version"],"predictions":{"H001":"field X differs before Normalize","H003":"no difference before Normalize"},"risk":"NONE"}
```

Result:

```json
{"id":"E001","phase":"RESULT","outcome":"Field X is already absent before Normalize in failing execution only","evidence":["O010"],"hypothesis_updates":{"H001":"strengthen","H003":"weaken"}}
```

## causal_set.json

```json
{
  "closure_status": "OPEN",
  "causes": [
    {
      "id": "C001",
      "hypothesis_id": "H001",
      "role": "PRIMARY",
      "mechanism": "...",
      "evidence": ["O003", "O010", "E001"],
      "independently_capable": true,
      "counterfactual_evidence": "..."
    }
  ],
  "relationships": [],
  "material_unresolved": [],
  "residual_unknowns": []
}
```

`closure_status` values:

- `OPEN`
- `SUFFICIENT_FOR_FIX`
- `REOPENED`

Roles may include `PRIMARY`, `CONTRIBUTING`, `LATENT_CONDITION`, `AMPLIFIER`.

## fix.json

```json
{
  "options": [],
  "selected_option": null,
  "selection_rationale": "",
  "invariants_preserved": [],
  "acceptance_tests": [],
  "implementation": {
    "status": "NOT_STARTED",
    "changes": [],
    "pre_change_snapshot": null
  }
}
```

## verification.json

```json
{
  "environment": {},
  "tests": [
    {
      "id": "T001",
      "fixture": "original-failing",
      "assertions": [],
      "result": "NOT_RUN",
      "evidence": []
    }
  ],
  "overall": "NOT_RUN",
  "unverified_risks": []
}
```

`result`: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`.

## closeout.md

Keep this human-readable. It should summarize the causal chain and verification, not reproduce raw logs.
