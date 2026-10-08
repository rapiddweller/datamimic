# Step 21: remove empty smoke-export wrappers

`SmokeExportRequest` now carries its existing rows and parameters directly.
The dry-run producer and exporter registry no longer construct and unwrap
no-invariant `RootModel` values. No descriptor, export algorithm, or row value
was changed. Amendment 62 records the two exact dynamic boundary positions.

Independent Luna implementation and QA passes were reviewed separately. The
new registry test preserves nested arbitrary Python values by identity and
checks exporter exceptions propagate; existing XML tests cover nested capture,
unsupported serialization, row-count mismatch, dispatch, and cleanup.

ArchKeel candidate report: 124 violations, 251 UNKNOWN positions before and
after the exact allowances. Without them, `IO-API-TYPES` adds two findings.
This is not architecture-green.

LOCAL VERIFIED: Ruff and full-package MyPy pass; 1419 unit tests pass
(11 skipped, 1 expected failure). The seeded nine-exporter XML descriptor
`issue_227_smoke_export_matrix.xml` produces equal products and smoke-export
counts at frozen Step 0 and here under the same code-level oracle. The CLI
dry-run JSON also matches after removing elapsed time. Focused QA tests pass
(14). Full descriptor inventory recapture remains open.

CI-ONLY VERIFICATION: not run.
