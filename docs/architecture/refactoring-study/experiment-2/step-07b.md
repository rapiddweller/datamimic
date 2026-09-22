# Step 07B: move file IO to its owner

## Change

- Moved file reading and content caching from the root `utils` package to `engine.io`.
- Exposed the two live file types through `engine.io.api`; internal IO callers use local modules.
- Moved project scaffolding to `interfaces.project` and deleted its unused `copy_file` helper.
- Removed the cache-miss debug message instead of retaining an IO-to-runtime logging dependency.

## Evidence

- ArchKeel violations: 1,008 -> 960.
- Baseline entries: 35 path-renamed findings added, 80 legacy findings removed.
- Cycle edges: unchanged at 181; root-layout remains 1 while five mixed-owner utilities remain.
- Remaining transitional crossings are explicit debt: 42 `domains -> io` and 1 `interfaces -> io`.
- Implementation tests: 149 focused tests, 5 weighted-source tests, and 44 CLI tests passed.
- Independent verification initially found one stale test import; after correction, 333 tests passed.
- Full unit suite: 1,113 passed, 11 skipped.
- Full package Ruff: pass.
- Full mypy reached 457 files and failed only on the two existing missing optional `ray` imports.
- Pinned ArchKeel 0.6.0 baseline validation: pass with no new baseline findings; target rules remain
  `FAIL` while 960 baseline violations remain.
- Descriptor oracle: 930 compared, 0 differences, 1 tolerated evidenced optional-shape variance.
  Statuses and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `17e8cb7160e2659e0533befbcdfbcd01a05ac929c07dc2a96c58f68ba5ddfc72`.

Service-backed tests remain unverified because the configured Podman machine is unavailable.
Step 7B is accepted as descriptor- and projection-equivalent to the frozen Step-0 oracle.
