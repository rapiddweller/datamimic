# Step 80: export metadata

IO owns `ExportMetadata`: the optional string controls `target_entity`, `selector`
and `type`. Runtime produces it; ExportSession carries it without changing the
two-/three-item tuple behavior. Routing accepts it and existing string mappings.
This is not runtime validation or a closed dictionary. Legacy exporter tuples
still erase types; full payload typing remains unfinished.

LOCAL VERIFIED: 1,542 clean-snapshot unit passes (11 skipped, 1 xfailed);
19 SQLite/file integration passes; both new characterization tests pass on
pristine Step 79. Ruff, MyPy (491 files), Pylint executable-cycle check, five
recursive-definition and four inner-target checks pass. Actual-source MyPy
consumer probes pass; three malformed metadata cases are rejected.

Released ArchKeel 0.8.1 reports clean FAIL 107 / counted UNKNOWN 157, versus
110 / 157 before. No baseline, budget, allowance, descriptor or oracle changed.
Independent Luna implementation and QA; Astra challenged and approved the
corrected input union. The full DSL oracle and report acceptance remain open.

CI-ONLY VERIFICATION: this checkpoint has not run yet. Step 79 CI passed its
executed test lanes, but failed architecture (110 / 157); E2E/release were skipped.
No merge or release.
