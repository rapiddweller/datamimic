# Amendment 21: source capabilities are DSL vocabulary

Date: 2026-09-28. Astra decision before the source-boundary migration.

`model/constraints/capabilities.py` contains immutable source-format and
source-mode facts, not validation logic. IO needs them for source routing, but
the root contract permits IO to depend only on DSL vocabulary. Move the whole
module to `dsl/vocabulary/source_capabilities.py`; update real imports, not an
old-path shim. Keep the existing catalog and projections together.

The target map and nested DSL layouts now declare that destination. The file
count stays 495. This does not widen IO's permissions or change DSL behavior.
The source and descriptor baselines remain frozen.

The same ownership review keeps `select_rows` and `select_row_iterator` in
`io/contracts.py`. They are neutral in-memory windows used by both source
readers and MemStore; moving them to `data_sources/selection.py` would create
an exporter-to-source dependency. Source distribution policy still moves to
`data_sources/selection.py`. No forwarding functions are added.
