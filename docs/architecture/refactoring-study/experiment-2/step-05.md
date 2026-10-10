# Step 05: consolidate IO

## Change

- Moved clients, connection configuration, data sources, and exporters under `engine.io`.
- Updated `engine.io.api`, internal callers, tests, and shipped demos.
- Removed all four legacy root packages; added no compatibility wrappers or behavior changes.

## Evidence

- ArchKeel violations: 1,110 -> 1,072.
- Cycle edges: 202 -> 184.
- IO placement violations: 34 -> 0.
- Root-layout violations: 12 -> 8.
- Baseline entries: 144 path-renamed findings added, 182 legacy findings removed. The additional
  removals are 34 IO-placement and 4 root-layout findings.
- Implementation tests: 199 passed.
- Independent tests: 223 unit and 64 staged integration tests passed.
- Full package Ruff: pass.
- Full mypy reached 461 files and failed only on the existing missing optional `ray` imports.
- No stale Python import of the four old namespaces remains.
- Descriptor oracle: 930 compared, 0 differences, 1 tolerated optional-shape variance. Statuses
  and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `7db921a746108e3634cab1fd362316205b10791f0d8e566c48e9860379500df1`.

The optional variance was `de_cities.population=null|int`. Twelve unchanged Step-0 reruns produced
both shapes, and the sibling integration test permits either value. The comparator now treats a
sampled `null` as optional for unseeded shape comparison; it still compares seeded output exactly.

Service-backed tests remain unverified because the configured Podman machine is unavailable.
Step 5 is accepted as behavior-equivalent to the frozen Step-0 oracle.
