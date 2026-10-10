# Step 08C8: route runtime through the DSL facade

## Change

- Published the existing cross-component DSL vocabulary through `engine.dsl.api` as identity
  re-exports.
- Routed every runtime dependency on DSL statements, enums, constants, constraints, and parsers
  through `engine.dsl.api` or `engine.dsl.contracts`.
- Kept DSL-internal imports on their concrete owner modules; no wrappers or replacement types were
  added.

## Evidence

- ArchKeel violations: 743 -> 586; 155 baseline fingerprints covering 157 imports resolved and 0
  added.
- Runtime -> DSL interface violations: 157 -> 0. Cycle edges remain 171.
- Independent fresh-process checks passed four import orders and verified identity for all 136
  imported facade bindings.
- Independent focused matrix: 215 passed. Implementation-focused matrix: 88 passed, 11 skipped.
- Full unit suite: 1,137 passed, 11 skipped.
- Full descriptor oracle: 930 compared with the prior commit; 0 differences and 0 tolerated shape
  variances. All four Authoring projection hashes are unchanged.
- Ruff, formatting check, and diff check pass. Full-package mypy reports only the two known missing
  optional Ray modules.

The facade currently exports the complete existing cross-component vocabulary: 66 names are used
by runtime; the remainder are existing Authoring, IO, and domain dependencies scheduled for the
next import-routing slices.
