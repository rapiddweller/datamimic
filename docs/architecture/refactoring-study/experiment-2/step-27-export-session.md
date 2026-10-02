# Step 27: separate exporter session state

Moved worker registration and page dispatch from the exporter registry to
`engine/io/exporters/session.py`. The session still calls the registry to
construct target exporters; `io.api.ExportSession` remains the runtime entry.
No export algorithm, exception path, or smoke-export wrapper changed.

LOCAL VERIFIED on isolated commit `724dbf4c`: 1,482 unit tests passed (11
skipped, one expected failure), 20 dispatch/architecture tests, three
descriptor-backed SQLite nested-export tests, five target-definition tests,
Ruff, full-package MyPy (491 files), Pylint cyclic-import check, and a `spawn`
worker import passed. ArchKeel parsed all
491 files and reports 108 violations, 176 UNKNOWN positions, and 86
baseline-new findings—unchanged from the preceding Finance commit. The
architecture gate remains red; this move clarifies ownership but does not
claim a numerical improvement.

The full descriptor oracle, service-backed tests, and CI have not been rerun
for this commit. The existing export-under-condition expected failure remains
separate from this ownership move.
