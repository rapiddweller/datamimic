# Step 13: IO owns page export

Amendment 52 publishes one `ExportSession` from IO. It owns worker-local target
registration, XML-to-JSON preparation, delete-order fact and page dispatch.
Runtime still chooses parent/child order. The unused page counter was removed.
No descriptor XML or public CLI behavior changed.

Independent Luna implementation and QA passes preceded root review. QA added
real-engine JSON chunk tests for single-process, multiprocessing and a later
single-to-multiprocess transition. A suspected nested-registration regression
was rejected after an isolated 2-parent/2-child run; nested writes are deferred
to the outer worker.

LOCAL VERIFIED: 1,334 unit tests passed, 11 skipped; Ruff, full-package mypy
(487 files), five architecture-definition tests and `git diff --check` passed.
Against the pre-step `066bd9f8` checkout, a seeded JSON descriptor produced
identical three filenames, rows and byte digest. An unseeded two-worker run
produced the same three filenames, five row IDs and field shape; its digest
differs and is not an equality requirement. The candidate ArchKeel report
shows 10 declared violations and 45 unknown positions; its new IO-interface
violation disappeared after the explicit contract entry. The pinned 0.8.0
cannot parse exact module declarations, so it is not a valid current gate.

CI-ONLY VERIFICATION: not run. Full descriptor parity and service-backed runs
remain open. Runtime still owns buffered finalization and publication; that is
the next IO-ownership slice, not a claim of completed architecture.
