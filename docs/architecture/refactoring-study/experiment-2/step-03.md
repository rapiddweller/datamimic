# Step 03: consolidate the DSL

## Change

- Moved `constants`, `enums`, `model`, `parsers`, and `statements` under `engine.dsl`.
- Updated internal imports; removed all five legacy root packages.
- Added no compatibility wrappers. No tracked documentation exposes the old imports.

The initial three-package move temporarily raised cycle edges from 219 to 225 because parsers and
statements still crossed the `engine` package boundary. The step was not accepted in that state.
Moving the complete DSL core reduced the final count to 213.

## Evidence

- ArchKeel violations: 1,274 -> 1,162.
- Cycle edges: 219 -> 213.
- DSL placement violations: 107 -> 0.
- Root-layout violations: 23 -> 18.
- Baseline entries: 385 path-renamed findings added, 497 legacy findings removed. Rule counts for
  moved findings are identical; the additional removals are 107 DSL-placement and 5 root-layout
  findings.
- Implementation tests: 573 passed.
- Independent serial verification: 586 passed, 11 skipped.
- Full package Ruff: pass.
- Full mypy reached 461 files and failed only on the existing missing optional `ray` imports in
  `tasks/generate_task.py` and `workers/ray_generate_worker.py`.
- No stale Python import of the five old namespaces remains.
- Descriptor oracle: 930 compared, 0 differences, 2 tolerated optional-shape variances. Statuses
  and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `63aaa1651907e621248233c850fad67dbb559c1cf5388290968a1c8fa397853c`.

Step 3 is accepted as behavior-equivalent to the frozen Step-0 oracle.
