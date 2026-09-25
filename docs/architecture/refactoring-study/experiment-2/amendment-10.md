# Amendment 10: retain four DSL/runtime attribute adapters

Date: 2026-09-23

## Decision

Keep `getattr` forbidden except in four exact adapter methods. The original blanket target
misclassified compatibility forwarding as accidental reflection; replacing it would change
existing DSL field, seeded-global, Faker-provider, or iterator-row access. No other magic
construct is exempted.

## Evidence

- `BaseEntity.__getattr__` preserves camelCase entity-field aliases; covered by
  `test_entity_field_alias_reads_the_declared_record_value`.
- `_EvalProxy.__getattr__` and `_SeededFaker.__getattr__` preserve seeded script-global and Faker
  provider access; covered by the expression-global replay, clock, rejection, and per-run Faker
  tests plus `test_seeded_script_globals_replay_identically`.
- `VariableIterator.__getattr__` preserves `row.field` access for iterator-backed storage,
  including non-dict rows; covered by `test_non_dict_row_attribute_access` and file-storage
  iterator tests.
- The contract uses exact function owners, not package prefixes; all other `getattr` calls remain
  forbidden, as do `Any`, casts, and the other listed control-flow constructs.
