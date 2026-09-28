# Step 14: IO owns buffered file lifecycle

Amendment 53 exposes IO operations for chunk finalization and artifact
publication. Runtime still selects worker IDs, traverses direct nested
`<generate>` statements, and runs two passes: finalize all, then publish all.
No descriptor or CLI surface changed.

Independent implementation and QA passes preceded root review. QA added real
engine checks for exact single-process JSON bytes, multiprocess completeness,
mixed JSON/CSV publication, nested direct children, and cleanup after a
finalization failure. The same focused tests against the older `066bd9f8`
checkout and this step returned 5 passed, 1 expected failure; the relevant
Runtime traversal was unchanged between `066bd9f8` and pre-step `718c06d0`.

Known defect: a `<generate>` under `<condition><if>` writes temporary JSON
but does not publish it. Both revisions exhibit this. The strict expected-
failure case is retained in `test_generate_export_lifecycle.py`. Fixing it
would change observable descriptor output and requires a separate behavior
amendment and parity review; it is not hidden as a passing artifact oracle.

LOCAL VERIFIED: 1,337 unit tests passed, 11 skipped, 1 expected failure;
133 serial functional tests and 12 exporter-matrix integration tests passed.
Ruff, full-package mypy (487 files), Pylint cyclic-import check, nine
architecture-definition tests, and
`git diff --check` passed. The candidate ArchKeel report still reports 10
declared violations and 45 unknown positions. Candidate validation is UNKNOWN
because it rejects declared public entries without importers; it also reports
9 baseline-new findings. Pinned 0.8.0 cannot parse exact module declarations.

CI-ONLY VERIFICATION: not run. Full descriptor parity and service-backed
integration remain open. The target architecture and report delivery are not
yet complete.
