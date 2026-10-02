# Step 83 — preserve setup defaults in smoke exports

Base: `501ca755f6e734583d79fd1dd1f7f4bddf18112c`.

Authoring now carries decoded setup separator/line-separator defaults through the existing IO smoke request. Existing exporters retain target-option precedence. Real runtime serialization and native values are unchanged.

The previous smoke check incorrectly accepted a CSV setup delimiter `||` that real execution rejected. It now reports DM002 and one failed exporter. Tests inspect actual smoke and runtime bytes for CSV/TXT defaults, empty fallback, overrides, nested targets and CRLF. No descriptor, oracle, architecture contract, allowance, budget or baseline changed.

Independent Luna implementation and BEFORE/AFTER QA; Astra approved the exact diff. Eight successful private cases have smoke/runtime byte equality; all nine runtime outputs and captures are unchanged. All observed smoke temp roots were removed. Final dryrun differs from the QA-tested source only by a comment, independently verified by SHA-256.

LOCAL VERIFIED: fresh root unit run 1,556 passed, 11 skipped, one xfail; Ruff and full MyPy (491 files). Two existing Pydantic warnings occur in Mongo/RDBMS no-port tests: expected str, got int value 0. Pylint executable-cycle, five recursive target and four inner target checks pass.

ArchKeel **0.8.1 release**: unchanged 106 violations / 157 counted UNKNOWN, baseline_new 69. Observation is complete; the contract gate is FAIL, not acceptance. This correction closes a verification defect, not architecture typing debt.

CI-ONLY VERIFICATION: parent run `36803105291` completed FAILURE at the architecture gate; all other executed jobs succeeded. E2E/release skipped. This checkpoint's CI is pending push.

Full DSL/EE parity and interactive Actual/Target/Diff acceptance remain open. Arbitrary runtime mutation of setup defaults is not covered. SQL/native converter policy slices remain separate, pending ArchKeel #228/#229. Merge and release remain on hold.
