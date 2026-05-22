# Project guidelines

## Tests
- Do **not** fix ruff/lint issues in `tests_ce/**`. Leave test-file lint alone.

## DATAMIMIC DSL models
- Always keep DATAMIMIC DSL models (the `.xml` descriptors used as test fixtures)
  **checked in**, even when they are generated from a builder. Committed DSL is far
  easier to review than in-memory generation. Pair each generated, committed model
  with a sync-check test that regenerates it and asserts it matches (so it can't rot).
