# Amendment 71: narrow the IO boundary

Date: 2026-09-29. Decision: Astra.

The original IO contract exposed five implementation details that no production
consumer imports through `io.api`: `DataSourceRegistry`, `ExporterConfig`,
`ExporterStateManager`, `UnifiedBufferedExporter`, and `create_exporter_list`.
The exporter session owns the runtime operation and calls the registry internally.
The names remain available at their owner modules; the nested exporter contract
retains its internal cross-component entries. Tests of those internals import
their owner directly.

Remove these five from the IO facade and parent-facing public lists. Keep
`Exporter`, `ExporterContext`, and `ExportSession` because their types and
operations cross the Runtime/IO boundary. This narrows the
contract without changing the target layout or descriptor behavior.
This contracts an undocumented Python import path. Amendment 22 and Amendment 40
did publish some of these names for the experiment; no current production
consumer or documented Python entry point uses them. External callers of these
undocumented re-exports would need to import from the owning module. This is
a source-level API contraction, not a type-safety improvement.
