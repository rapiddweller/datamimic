# Amendment 217 — remaining IO boundary types

2026-11-28. [Owner decision for #779][decision] and independent architecture
review. Base `516bd686`.

- `MemstoreRow: TypeAlias = dict[str, object]` in `engine/io/contracts.py` describes a
  mutable row with DSL-defined columns and native cell values. The two
  concrete Memstore getters and both `MemstoreSource` getters return
  `list[MemstoreRow]`. The list is live when returned and may be replaced by a
  write or reconciliation; surviving row objects are retained.
- `RdbmsConnectionValues: TypeAlias = dict[str, object]` is the return type
  of `RdbmsConnectionConfig.get_connection_config`. It describes the full
  normalized connection dump, including user-supplied engine options. The
  RDBMS client filters those options through `_ENGINE_KWARGS`.

Runtime's Build readback returns `Sequence[object] | None`. The verifier
compares length and ordered row values. `None` means the target is not a
memstore; an empty sequence is a real readback. For multiple targets, a
matching readback from any memstore still suffices.

Use two exact `IO-API-TYPES` selectors per row: one for the open map
without `container_depth`, and one for its native cells at the specified
depth. Each `qualified_name` starts with `datamimic_ce.engine.io.api.`,
`position` is `"return"`, and `field_path` is `""`. Update the two
`MemstoreSource` positions from Amendment 181 to name the alias; their
map and cell selector scopes remain the same.

| Qualified suffix | Complete annotation | Cell `container_depth` |
| --- | --- | --- |
| `Memstore.get_all_data_by_type` | `list[MemstoreRow]` | `2` |
| `Memstore.get_data_by_type` | `list[MemstoreRow]` | `2` |
| `MemstoreSource.get_all_data_by_type` | `list[MemstoreRow]` | `2` |
| `MemstoreSource.get_data_by_type` | `list[MemstoreRow]` | `2` |
| `RdbmsConnectionConfig.get_connection_config` | `RdbmsConnectionValues` | `1` |

This supersedes Amendment 181's statement that the concrete Memstore getters
remain unannotated. CE leads; EE adopts the two aliases later.

The approved CE-only `RandomRowsByColumnsClient` structural protocol remains
deferred. It will introduce a shared `ColumnRow: TypeAlias = tuple[object, ...]`
and return `list[ColumnRow]` from its positional-only
`get_random_rows_by_columns` method.
`Memstore.removeNotExistingIds` keeps its unannotated client and direct call,
retaining surviving row objects. EE keeps `get_ordered_rows_by_columns`
without the CE protocol.

The gate decision depends on [archkeel#2222][alias-fix] for alias resolution and
[archkeel#2220][tuple-fix] for nested selectors. PR #808 merges only after the
ArchKeel 5 upgrade can decide the named return positions and counterprobes show
that it rejects missing allowances and allowances with the wrong depth or
position.

[decision]: https://github.com/rapiddweller/datamimic/issues/779#issuecomment-7234033354
[alias-fix]: https://github.com/rapiddweller/archkeel/issues/2222
[tuple-fix]: https://github.com/rapiddweller/archkeel/issues/2220
