# Amendment 203 — selector-backed variable rows

2026-10-10. Decision: agent, delegated by Astra. Base `9e6667e1`.

IO owns query reads and page/cyclic selection; Runtime owns selector evaluation
and execution timing (`inner/target.md:155`). Built-in SQL queries return ordered
maps with query-selected column names; Mongo queries return documents. Native
Decimal, date, bytes and nested cells make a fixed DTO or JSON conversion wrong.
Amendment 181 deferred Iterables and did not grant this return permission.

Change only `read_variable_query`'s return annotation to
`list[dict[str, object]]`; preserve its executable body. Append exactly two
`IO-API-TYPES.allowed_positions` selectors, preserving all earlier entries:

```json
[
  {
    "qualified_name": "datamimic_ce.engine.io.api.read_variable_query",
    "position": "return",
    "field_path": "",
    "annotation": "list[dict[str, object]]"
  },
  {
    "qualified_name": "datamimic_ce.engine.io.api.read_variable_query",
    "position": "return",
    "field_path": "",
    "annotation": "list[dict[str, object]]",
    "container_depth": 2
  }
]
```

The first allows the single native row map; the second accepts cell opacity.
This is an explicit target widening, not full type closure or serializability.
Injected DatabaseClient subclasses can still return scalar lists: their identity,
values and native exceptions stay unchanged. External typed callers and custom
client row contracts remain UNKNOWN; the narrower mutable return annotation can
reject previously accepted wider static contracts.

Generic file/memstore `read_variable_source` remains iterable and may contain
scalars. No runtime checks, casts, copies, client retyping, dependency/ownership,
baseline, oracle, EE or transport changes. Native SQLite and Mongo driver-seam
checks establish local row behavior; full Mongo service parity remains unproven.

LOCAL VERIFIED: old-source behavior 80 PASS; signature and selector guards RED,
then 185 focused checks PASS. Unit suite: 2399 PASS, 11 skipped, 1 xfailed.
Package Ruff, full MyPy (488 files), 13 definition checks and executable AST PASS.
Pinned ArchKeel 1.1.1: FAIL12 (13 → 12); all remaining findings, 254 canonical /
200 measured UNKNOWNs, dependency/owner facts and 488/488 coverage preserved.
Receipts: `/tmp/ce-step203-receipts/`. CI-ONLY VERIFICATION: none performed.
