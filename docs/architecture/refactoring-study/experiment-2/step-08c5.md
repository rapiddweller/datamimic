# Step 08C5: construct connections at runtime

## Change

- Removed IO connection configs from database and MongoDB DSL statements.
- Deleted the unused eager MongoDB client construction during parsing.
- Runtime setup tasks now construct IO configs and clients through `engine.io.api`.

## Evidence

- ArchKeel violations: 791 -> 785; `INTERFACES-ONLY` 450 -> 447 and
  `REQUIRES-COMPLETE` 24 -> 21. No new baseline fingerprint.
- Unresolved calls improve 1,407 -> 1,404; cycle edges remain 172.
- Implementation verification: 20 passed. Independent verification: 20 passed.
- Full unit suite: 1,122 passed, 11 skipped.
- Full package Ruff, targeted mypy, and diff check: pass.
- Full mypy checked 460 files and failed only on the two existing missing optional `ray` imports.
- Descriptor oracle: 930 compared, 0 differences, 1 optional-shape variance tolerated. Statuses
  and all four projection hashes match Step 0. Snapshot SHA-256:
  `86ab7ea0fde31f447a021d2b80478cb8f20570b3c61d6f60f7197184d042fbeb`.

For an invalid direct `DatabaseStatement` whose model has no database name, validation now fails
when its task builds the IO config instead of during statement construction. No tracked caller or
descriptor relies on that undocumented timing. Service-backed database tests remain unverified
because the configured Podman machine is unavailable.
