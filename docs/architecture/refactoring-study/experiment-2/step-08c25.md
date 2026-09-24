# Step 08C25: remove two duplicate authoring tests

## Change

- Removed `test_every_fixture_produces_diagnostics`. The 28 parametrized
  `test_fixture_reports_seeded_rules` cases already lint the same fixtures and
  require each fixture's non-empty expected rule set to appear. This implies
  diagnostics exist without a second 28-fixture pass.
- Removed the older service-level `dry_run=False` rejection test from
  `test_scaffold_contracts.py`. `test_service_gateway.py` still checks the
  same `ScaffoldRequest` validation with the more precise
  `ValidationError`. The separate CLI `--no-dry-run` exit-code test remains.
- No production, XML, fixture, contract, or baseline change.

## Evidence

- Implementation and independent review selected the two duplicates
  separately, then checked the final diff. The reviewer confirmed no lost
  predicate or uncovered fixture and exercised 82 focused tests before the
  second deletion.
- Current authoring unit suite after both deletions: 438 passed. The implementation agent's
  post-deletion focused service/scaffold run: 41 passed. Ruff,
  full-package MyPy, and `git diff --check` pass.
- The architecture gate remains pinned and fail-closed; this is a test-hygiene
  change, not runtime-equivalence evidence.
