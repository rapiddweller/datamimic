# Step 08C17: type runtime control flow

## Change

- Moved expression evaluation and script execution to their two declared Runtime owners.
- Typed runtime contexts, sources, generators, tasks, workers, converter calls, and optional
  Ray/dill boundaries.
- Added one domain-owned `RandomSource` protocol shared by domain and runtime code.
- Replaced factory wall-clock duration measurement with the monotonic clock.
- Typed the domain entity cache and the exrex boundary without changing legacy alias behavior.

## Evidence

- ArchKeel violations: 91 -> 4; no dynamic-execution, dependency, cycle, or boundary-type
  violations remain.
- Measurements: calls unresolved 1,397 -> 1,288; cycle edges remain 171; private crossings remain
  0; typing positions 350 -> 144.
- Unit suite: 1,167 passed, 11 skipped. The independent Runtime review passed 100 tests with 11
  skips; its four remaining-reflection review passed 45 focused tests.
- Serial API/factory/functional/integration/architecture run: 2,577 passed, 17 skipped. Its two
  failures were isolated: the sandbox blocked a local SSE socket (the isolated unsandboxed test
  passed), and the factory used the wrong clock for duration (fixed; clock/factory rerun 469 passed).
- OrbStack external gate: 152 passed, 10 skipped; the six failures were only stale local
  MSSQL/Oracle ports and credentials. With the two local fixture files temporarily pointed at the
  running services, all six passed; the fixture edits were reverted.
- Full-package mypy and package Ruff pass.
- Integrated descriptor oracle: 930 compared, 0 differences, 0 shape variances. Counts remain 454
  captured, 62 expected-error, 16 non-descriptor, 76 unrunnable, and 322 unverified. All four
  Authoring projection hashes match Step 0.

## Product decision required

The four remaining findings are the compatibility adapters for normalized legacy entity aliases,
seeded expression-module forwarding, seeded Faker providers, and iterator `row.field` access.
Removing them narrows existing DSL behavior. The frozen contract is not weakened without an
explicit decision.
