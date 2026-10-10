# Step 114: restore the SQL target capability description

Base source: `6433321f`. Commit `0edf29a6` changed
`ExecuteModel.target.description` outside Amendment 60's seven wording changes
and the approved transition metadata. Astra reconstructs the original frozen
manifest exactly and approves restoring this one field. It still describes
the preserved injected-client lookup and positional `execute_sql_script` call.
No runtime, validator, version, target, oracle or baseline changes.
Independent Luna implementation and QA; one published-manifest assertion.

LOCAL VERIFIED: **2,295 units passed, 11 skipped, one existing xfail**;
two existing Pydantic warnings. 122 implementation controls, 43 independent QA controls and
32 root SQL/reference checks pass; full MyPy (491 files), Ruff and source
formatting pass. Existing reference-test formatting debt is untouched.
All other 490 source files are unchanged. Parsed capability JSON changes at
exactly `elements.execute.attributes.target.description`; compiler and both
reference projections retain identical content, byte counts and hashes.

The 931 inventory entries and **13 selected result records** remain identical.
The comparator exits 1 for the two existing incomplete captures and the intended
repair of the previous capability output. The original raw frozen hash remains
**FAIL** for separate version/approved-output differences. The historical
comparator bridge expects a later `dev89` recapture; the original frozen hash
was produced with version `4.1.0`. Neither baseline nor allowance is extended.

The console and recorder expose different distribution metadata (`dev246` from
venv site-packages; `dev288` from source-directory metadata). Their parsed
manifests differ only in `schema_version`. Before/after recorder profiles match;
raw hashes from different invocation profiles are not interchangeable.

Fresh published ArchKeel 1.0.0 remains **89 violations / 200 measured UNKNOWNs /
two cycle edges**, observing 491/491 files. No finding or UNKNOWN ID changes.
Overall target, full DSL and report acceptance remain open.

CI-ONLY VERIFICATION: no passing remote result claimed for this slice.
Evidence: `/tmp/ce-resume-20261008/sql-description/` and `capabilities-audit.md`.
