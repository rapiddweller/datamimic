# Step 08C12: establish the typed IO facade

## Change

- Routed every cross-component IO import through `engine.io.api` or `engine.io.contracts`.
- Kept the buffered-exporter registry private and moved smoke-export execution behind a typed IO
  request.
- Moved descriptor-property loading behind `runtime.api`, removing the interfaces-to-IO edge.
- Activated `IO-API-TYPES` and the frozen IO contracts module.

## Evidence

- ArchKeel violations: 347 -> 321; 24 baseline fingerprints resolved, 0 added.
- Remaining boundary violations: 8. `private_crossings`: 2 -> 0. Component graph remains acyclic.
- Implementation gate: 866 passed, 11 skipped. Independent gate: 194 unit, 65 CLI/file-export,
  and 2 shipped demo tests passed.
- Full descriptor oracle: 930 compared with Step 08C11, 0 differences and 3 permitted unseeded
  optional-shape variances. All four Authoring projection hashes are unchanged.
- Ruff and diff check pass. Full-package mypy reports only the two known missing optional Ray
  imports; suppressing only `import-not-found` leaves no type errors across 469 files.

The 322 descriptors requiring unavailable or unconfigured external conditions remain unverified
by the oracle. The prior OrbStack MongoDB/PostgreSQL service gate remains the latest live service
evidence.
