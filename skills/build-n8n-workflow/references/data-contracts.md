# Data contracts

Define contracts at boundaries that can change independently: trigger ingress, normalization, sub-workflow interfaces, database persistence, external API output, and final result.

## Contract fields

For each field record where relevant:
- name;
- type;
- required;
- nullable;
- allowed values;
- semantic meaning;
- units;
- timezone;
- identifier domain;
- provenance/source;
- confidence;
- version.

## Null is not missing

Distinguish:
- field absent;
- explicit null;
- empty string;
- empty array/object;
- zero/false.

If downstream behavior differs, encode that difference.

## Cardinality

Specify whether a boundary yields:
- zero or one item;
- exactly one item;
- zero to many items;
- one aggregate item containing an array.

Do not switch between "many n8n items" and "one item containing an array" casually. They affect expressions, merges, loops, and item linking.

## Canonicalization

Normalize unstable source labels once. Preserve:
- raw value when auditability matters;
- canonical value;
- mapping/version if mappings evolve.

## Cross-workflow contracts

Treat the output of a reusable sub-workflow like an API. Keep fields stable, version breaking changes, and avoid exposing internal node names as contract semantics.

## Identifiers

Prefer explicit stable IDs. If an identifier is used for deduplication, define its scope and collision semantics.

## Validation

Validate important external inputs at or near ingress. Fail or quarantine invalid records deliberately instead of allowing malformed shapes to propagate until a distant node fails.
