# Amendment 209 — exact native variable-source return

2026-10-10. Decision: agent, delegated by Astra.
Base `6ef3e3ec7bbfda06a7378a5f182db3479b2dbe75`.

Append one root `IO-API-TYPES.allowed_positions` selector:

```json
{
  "qualified_name": "datamimic_ce.engine.io.api.read_variable_source",
  "position": "return",
  "field_path": "",
  "annotation": "Iterable[object] | None",
  "container_depth": 1
}
```

File/database/Memstore reads carry native values, scalar JSON list items and
iterators. Preserve their identity, errors, precedence and existing paging.
A map DTO or JSON coercion would change this boundary. The facade reexports
`engine/io/data_sources/variable.py`; Runtime retains source policy.

This accepts one opaque element; type closure and serialization remain unproven.
`VariableSourcePlan.data`, aliases, wrappers and other native positions receive
no permission. No production source, annotation, nested contract, baseline,
A155 SQL, worker-local client, environment-property or sealed DSL change.

Explicit noncyclic pages defer consumption. Absent pagination consumes input
to determine length; cyclic file selection materializes and repeats its page.
These existing limits remain; universal laziness is not promised.

Published ArchKeel 1.1.2 was independently accepted before this change.
Native amendment writing/validation may still refuse retained usage UNKNOWNs;
the companion digest-bound amendment is not native-writer success or target PASS.
