# Step 15: IO owns lazy output writes

Amendment 54 moves test-result capture and memstore writes behind IO operations.
Runtime still owns zero-count decisions, worker merge, target-statement
traversal, and the order of capture, memstore, finalization, and publication.
No descriptor or CLI surface changed.

Independent Luna implementation and QA passes preceded root review. QA found
an import-time annotation error in the first implementation. Root review then
used the candidate ArchKeel graph to reject a type-only dependency from
exporter core to concrete memory/diagnostic exporters: it added two dependency
violations and one cycle. The final code checks concrete exporter types at the
IO boundary without that cycle; negative tests cover both checks.

Eight real-descriptor capture/memstore tests passed against both the older
`066bd9f8` checkout and this step. They cover SP/MP rows, zero-count products,
and direct/conditional nested capture. The relevant lazy-write code was
unchanged between `066bd9f8` and pre-step `75872848`. The existing
conditional-child *file* publication defect remains the strict expected
failure from Step 14.

LOCAL VERIFIED: 1,347 unit tests passed, 11 skipped, 1 expected failure;
133 serial functional, 12 exporter-matrix integration, and nine architecture
definition tests passed. Ruff, full-package mypy (487 files), Pylint
cyclic-import check, and `git diff --check` passed. Eight focused descriptor
cases had the same results on old and new code. Candidate report has 10
declared violations, 2 cycle edges, and 47 unknown positions. Two new UNKNOWN
positions are the fully annotated generic product mappings on the new IO API
functions. They are analyzer type-resolution limits, not evidence of correct
behavior. The existing 45 UNKNOWN positions and 10 violations remain open.
Candidate validation returns UNKNOWN because declared public entries without
importers remain invalid; it also reports 9 baseline-new findings.

CI-ONLY VERIFICATION: not run. Full descriptor parity, service-backed tests,
and the final target/report acceptance remain open.
