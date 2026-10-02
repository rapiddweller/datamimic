# Step 67: repair clean-checkout gates

CI run 36589307991 exposed three failures hidden by the dirty working tree:
`sources/length.py` and `sequence_table.py` needed Optional-safe values after
typed DSL accessors; the target-map test rejected the intentionally empty root
`__init__.py`; the no-locales test watched a path already relocated to
`domains/shared/datasets/locales`. The fixes narrow values, allow only an
empty root initializer, and check the versioned locale directory for JSON.

LOCAL VERIFIED: 61 focused tests, full-package MyPy (491 files), targeted Ruff,
and staged diff check passed. Independent QA then caught the stale locale path;
that correction needs a fresh CI run. DB-backed sequence parity remains open.
