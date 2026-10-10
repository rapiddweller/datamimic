# Step 61: type ExecuteStatement accessors

`ExecuteStatement.uri` and `.target` now declare `str | None`, matching their
existing model fields and guarded runtime use. No descriptor or execution
behavior changed. EE keeps its edition-specific `DslOpenString | None` type.

LOCAL VERIFIED: 17 focused unit/integration Execute tests passed, including
invalid and missing input cases. Full-package MyPy (491 files), Ruff, and
`git diff --check` passed. The candidate ArchKeel report observed 491/491
modules: UNKNOWN positions 163 → 161, with exactly the `uri` and `target`
missing-annotation IDs removed; all 121 violation IDs were unchanged.
Independent Luna QA traced model, parser, runtime, and positive/negative DSL
cases and found no change to the public or execution contract.
CI-ONLY VERIFICATION: not run. Full descriptor equivalence and service-backed
tests remain open.
