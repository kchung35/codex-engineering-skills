# Assertion contract

Assertions are deterministic rules applied to captured execution JSON.

## Envelope

```json
{
  "schema_version": 1,
  "assertions": [ ... ]
}
```

## Supported types

### `status_equals`

```json
{"type": "status_equals", "expected": "success"}
```

Compares the execution's top-level `status`.

### `node_executed`

```json
{"type": "node_executed", "node": "Normalize"}
```

Passes when `data.resultData.runData` contains at least one run for the node.

### `node_not_executed`

```json
{"type": "node_not_executed", "node": "Send Email"}
```

Useful for negative routing assertions.

### `node_error_absent`

```json
{"type": "node_error_absent", "node": "Normalize"}
```

Fails when any recorded run for the node contains a non-null `error`.

### `node_item_count`

```json
{"type": "node_item_count", "node": "Normalize", "run_index": 0, "output_index": 0, "expected": 5}
```

Counts items in `data.main[output_index]` for the selected node run.

### `json_pointer_exists`

```json
{"type": "json_pointer_exists", "pointer": "/data/resultData/runData/Normalize/0/data/main/0/0/json/fund_id"}
```

Uses RFC 6901 JSON Pointer syntax.

### `json_pointer_equals`

```json
{"type": "json_pointer_equals", "pointer": "/status", "expected": "success"}
```

Deep equality; values are compared as JSON values, not strings.

### `json_pointer_not_equals`

```json
{"type": "json_pointer_not_equals", "pointer": "/data/resultData/error/message", "expected": "old error"}
```

### `json_pointer_matches_regex`

```json
{"type": "json_pointer_matches_regex", "pointer": "/data/resultData/error/message", "pattern": "timeout|rate limit", "flags": "i"}
```

The pointer value must be a string.

### `json_pointer_length`

```json
{"type": "json_pointer_length", "pointer": "/data/resultData/runData/Normalize", "expected": 1}
```

Works on arrays, objects, and strings.

## Oracle discipline

Assertions should express the semantic contract, not incidental implementation detail. Prefer asserting canonical output fields and branch behavior over exact timing values or entire raw payload equality.

A test can contain many assertions. The overall case passes only when every assertion passes.
