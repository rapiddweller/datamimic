# Step 08C1: move generator orchestration to runtime

## Change

- Moved `GeneratorUtil` from domain literals to `engine.runtime.generators.factory`.
- Removed the production UUID test helper; tests use the equivalent stdlib predicate directly.
- Changed `IncrementGenerator` pagination to primitive `skip` and `limit` values, removing its IO
  dependency.
- Activated narrow DSL and domain APIs. The domain API exposes a typed iterator, not the internal
  registry dictionary.

## Evidence

- ArchKeel violations: 831 -> 817; `INTERFACES-ONLY` 473 -> 464,
  `REQUIRES-COMPLETE` 37 -> 33, and `NO-MAGIC-CONTROL-FLOW` 312 -> 311.
- Cycle edges remain 177; unresolved calls remain 1,408; typing positions improve 461 -> 460.
- `DOMAIN-API-TYPES`: pass with its one signature position decided and none undecided.
- Implementation verification: 71 passed, 11 skipped. Independent verification: 73 passed.
- Full unit suite: 1,117 passed, 11 skipped.
- Full package Ruff, focused import ordering, and diff check: pass.
- Full mypy reached 457 files and failed only on the two existing missing optional `ray` imports.
- Descriptor oracle: 930 compared, 0 differences, 3 optional-shape variances tolerated. Statuses
  and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `10b916276cef180642939b7bd20932c1cd73194fe6439ab1ac272edba1fc4db8`.

The first full oracle run lost one multiprocessing child result despite exit 0. That descriptor
matched Step 0 in three isolated runs; a complete rerun at four-way parallelism passed. Two new
baseline fingerprints are the six existing forbidden constructs relocated with the factory, while
15 old fingerprints resolve; no new boundary violation remains. Service-backed tests remain
unverified because the configured Podman machine is unavailable.
