# Step 28: publish the IO memstore provider type

`ExporterContext.memstore_manager` already returns IO's `MemstoreProvider`.
`io.api` now re-exports that existing protocol. No behavior, contract permission,
or target ownership changed.

LOCAL VERIFIED: the fresh ArchKeel report removes exactly the
`ExporterContext.memstore_manager returns MemstoreProvider which io does not declare`
finding (119 → 118 violations); there are no new violation messages and measured
UNKNOWN positions remain 237. Observation and target coverage pass (489/489 files).
The target report still has one non-empty responsibility for each of 149
components and 489 modules. `make lint typecheck` passes; 22 focused
architecture/memstore tests pass. Independent QA ran 34 memstore/dispatch tests
(1 expected failure) and a temporary MyPy probe that accepts a conforming
provider and rejects `get_memstore -> object` with normal import following.
No DSL descriptor comparison was repeated for this type-only facade export.

The baseline gate remains UNKNOWN: 13 inherited-generic `interface.unused`
diagnostics from ArchKeel #204. `baseline_new` is 89, not a pass. The 118
remaining declared violations and 237 measured UNKNOWN positions remain open.
CI-ONLY VERIFICATION: not run.
