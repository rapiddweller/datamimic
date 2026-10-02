# Step 08C7: establish typed execution boundaries

## Change

- Moved property-file parsing into DSL and made runtime-environment selection an explicit parser
  input.
- Removed IO dependencies on runtime and domains through narrow exporter and entity contracts.
- Centralized the parse-and-run lifecycle in runtime and routed Python, factory, CLI, and Authoring
  adapters through typed APIs.
- Activated boundary-type rules for `runtime` and `interfaces`.

## Evidence

- ArchKeel violations: 784 -> 743; 38 baseline fingerprints resolved and 0 added.
- Component cycles: 1 -> 0; cycle edges: 172 -> 171.
- Unresolved calls: 1,404 -> 1,403; typing positions: 458 -> 454.
- Unit suite: 1,137 passed, 11 skipped.
- Full descriptor oracle: 930 compared with Step 0; 0 differences and three permitted unseeded
  optional-shape variances. All four Authoring projection
  hashes are unchanged.
- Ruff and diff check pass. Full-package mypy reports only the two known missing optional Ray
  modules.
- Independent Luna verification: 152 serial tests passed across the Python API, runtime, DSL,
  Authoring dry-run, CLI, include, factory, SQLite, clients, secure XML, and exporters.
- OrbStack service verification: 63 passed and 8 skipped across the selected MongoDB and RDBMS
  suites. Four unrelated MSSQL/Oracle reference tests could not connect because CE expects
  `localhost:1433/1521`, while the running containers publish `41433/41521`.

The service run exposed and the slice fixed one real regression: `SetupParser` had its explicit
runtime environment reset to `production` by its base initializer. MongoDB and PostgreSQL paths
are verified against the existing OrbStack services; MSSQL and Oracle remain environment-blocked.
