# Step 02: source routing belongs to runtime

## Change

- Moved statement/context-aware source routing to `engine.runtime.sources`.
- Kept file/client mechanics in `data_sources`; exposed current IO types through `engine.io.api`.
- Moved `ChunkSourceReader` to runtime.
- Replaced variable-plan string dispatch with `VariableSourcePlanKind`.
- Removed the brittle source-text architecture test; ArchKeel owns placement checks.

`DataSourceRegistry` remains a transitional IO API export because runtime still uses its file readers
and selection helpers. No forwarding wrappers were added. Splitting selection policy from file IO is
remaining work, not hidden by this step.

## Evidence

- ArchKeel violations: 1,305 -> 1,274.
- Cycle edges: 243 -> 219.
- `INTERFACES-ONLY`: 576 -> 554.
- `REQUIRES-COMPLETE`: 120 -> 113.
- Dynamic execution violations: 11 -> 10; the removed `eval` now uses the runtime evaluator.
- The baseline update had 34 new and 64 resolved fingerprints. All 34 new fingerprints are moved
  DSL/interface/type facts in `engine.runtime.sources`; no new construct or dependency permission was
  introduced.
- Serial focused unit tests: 100 passed, 11 skipped.
- Serial affected functional/integration tests: 26 passed.
- Full package Ruff: pass.
- All four oracle projections: unchanged from Step 0.
- Full mypy reached 461 files and failed only on the existing missing optional `ray` imports in
  `tasks/generate_task.py` and `workers/ray_generate_worker.py`.
- Descriptor oracle: 930 compared, 0 differences, 1 tolerated optional-shape variance. Statuses
  were identical: 454 captured, 62 expected errors, 16 non-descriptors, 76 unrunnable, and 322
  unverified. Step-2 snapshot SHA-256:
  `00aeaf68a2cee791d8aac37a4bcf970135a06ef726fc116b36d00381580e1c23`.

Step 2 is accepted as behavior-equivalent to the frozen Step-0 oracle.
