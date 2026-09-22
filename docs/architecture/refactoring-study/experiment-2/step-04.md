# Step 04: consolidate the runtime

## Change

- Moved configuration, contexts, logging, in-memory storage, tasks, and workers under
  `engine.runtime`.
- Updated internal and shipped-demo imports; removed all six legacy root paths.
- Added no compatibility wrappers and made no behavior changes.

`utils` deliberately remains visible. It mixes several owners and will be decomposed instead of
becoming a new `engine.runtime.utils` package.

## Evidence

- ArchKeel violations: 1,162 -> 1,110.
- Cycle edges: 213 -> 202.
- Runtime placement violations: 66 -> 20.
- Root-layout violations: 18 -> 12.
- Baseline entries: 320 path-renamed findings added, 372 legacy findings removed. The additional
  removals are 46 runtime-placement and 6 root-layout findings.
- Implementation serial tests: 104 passed, 11 skipped.
- Independent full serial unit suite: 1,152 passed, 11 skipped.
- Full package Ruff: pass.
- Full mypy reached 461 files and failed only on the existing missing optional `ray` imports in
  `engine/runtime/tasks/generate_task.py` and `engine/runtime/workers/ray_generate_worker.py`.
- No stale Python import of the six old namespaces remains.
- Descriptor oracle: 930 compared, 0 differences, 2 tolerated optional-shape variances. Statuses
  and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `65afd4094d277591819578dc10ad99b82998cc2ac735039086aa3e3e3a8a404c`.

Step 4 is accepted as behavior-equivalent to the frozen Step-0 oracle.
