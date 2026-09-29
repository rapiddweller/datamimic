# Step 30: execute local SQLite descriptors in the oracle

The descriptor inventory previously classified every `<database>` as an
external service, including local SQLite files staged into temporary directories.
It now exempts only descriptors whose database clients all say `dbms="sqlite"`.
The external-service suite path and any remote, mixed or unknown client remain
gated. Independent QA added 13 positive/negative classification cases.

Of 930 tracked XML files, 49 SQLite-only integration descriptors are no longer
misclassified as external-service. Forty-one have the normal runnable category;
eight retain another category such as intentionally invalid. The same current
oracle captured those 49 against clean control `066bd9f8` and the target
checkout: each side produced 39 CAPTURED, eight EXPECTED-ERROR, one UNRUNNABLE
and one UNVERIFIED. Forty-seven descriptor pairs compare equal. The phase-two
delete descriptor needs its phase-one setup, and one memstore descriptor lacks
the oracle's nested-list cardinality proof. The corresponding current integration
suites pass (eight tests), but those two Alt/Neu results remain unproved.

The comparator still reports a separate capabilities-projection difference
between the control checkout and target; this step did not change the target's
four projection hashes. It did not execute the remaining 228 externally gated
descriptors. Full DSL equivalence is therefore still open.

LOCAL VERIFIED: oracle and comparator self-tests, 13 focused classification
cases, Ruff, full-package MyPy, 1,442 unit tests (11 skipped, one expected
failure), and the 49-case Alt/Neu capture/comparison.
CI-ONLY VERIFICATION: not run. The 49-case parity claim remains provisional
while the full architecture and descriptor gates are open (ArchKeel #204).
