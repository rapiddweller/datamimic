# Step 07A: remove owner-obvious root utilities

## Change

- Moved demo handling to `interfaces`, XML and time-series semantics to `engine.dsl`, runtime
  observability and record helpers to `engine.runtime`, and domain algorithms to `domains`.
- Moved the package-version lookup beside the determinism proof that consumes it.
- Deleted commented-only `field_generator`, unused `sanitize_dict` and `get_last_commit_info`, and
  the uncalled `XMLValidator` / `safe_parse_generator_param` module plus its isolated test.
- Left file loading, sampling, and dynamic plugin utilities for separate semantic steps.

## Evidence

- Repository-wide caller review found no production caller for any deleted symbol.
- ArchKeel violations: 1,033 -> 1,008.
- Runtime placement violations: 20 -> 8.
- Baseline entries: 19 path-renamed findings added, 45 legacy findings removed.
- Cycle edges: unchanged at 181; root-layout remains 1 while the seven mixed-owner utilities remain.
- Implementation tests: 701 passed, 11 skipped across focused, authoring, and clock-drift suites.
- Independent focused tests: 173 passed.
- Full package Ruff: pass.
- Full mypy reached 456 files and failed only on the two existing missing optional `ray` imports.
- Pinned ArchKeel 0.6.0 baseline validation: pass; target rules remain `FAIL` while 1,008
  baseline violations remain.
- Descriptor oracle: 930 compared, 0 differences, 2 tolerated evidenced optional-shape variances.
  Statuses and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `e585fc1456f04e0a06cb23e31713a8e9328b02e33a83bdffe38178f2cecaff32`.

The first oracle run reported a capability-version drift. The cause was an ignored
`datamimic_ce.egg-info` directory created by the preceding wheel inspection, not production code.
Removing the generated build metadata restored the frozen projection hash. The clean full rerun is
the accepted result.

Service-backed tests remain unverified because the configured Podman machine is unavailable.
Step 7A is accepted as behavior-equivalent to the frozen Step-0 oracle.
