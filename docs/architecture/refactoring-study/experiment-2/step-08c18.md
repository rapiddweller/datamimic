# Step 08C18: isolate XLSX test fixtures

## Change

- Five existing XLSX integration tests now share one function-scoped workbook
  fixture and its teardown. Assertions and descriptor bytes are unchanged.
- The fixture removes stale output before a case and cleans workbook/output
  after success or failure. No production code or architecture rule changed.

## Evidence

- Independent implementation pass; orchestrator reviewed the diff.
- XLSX integration directory: 15 passed with the project venv and
  `-p no:rerunfailures` (the default plugin could not bind localhost in the
  sandbox). Package Ruff and full-package MyPy pass (474 source files).
- ArchKeel 0.6.1 `validate --baseline` and `--against eafc119f` pass:
  474/474 files, no new or resolved violations, `declared_rules=PASS`.
- `make lint` remains red at Pylint, as before this test-only change. It is
  not reported as a passing delivery gate.

No new descriptor parity claim follows from this test refactor; the frozen
Step-0 oracle and separate service ledger remain the behavioral evidence.
