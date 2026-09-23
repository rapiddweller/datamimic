# Step 08C9: route Authoring through the DSL facade

## Change

- Routed every Authoring dependency on DSL statements, enums, constants, constraints, parsers,
  schema facts, and XML helpers through `engine.dsl.api` or `engine.dsl.contracts`.
- Changed imports only. The DSL facade required no additional export.

## Evidence

- ArchKeel violations: 586 -> 434; 136 baseline fingerprints covering 152 imports resolved and 0
  added.
- Authoring -> DSL interface violations: 152 -> 0. Cycle edges remain 171.
- Authoring suite: 433 passed. Independent focused matrix: 215 passed.
- Independent fresh-process checks passed four import orders and verified identity for all 136
  imported DSL facade bindings.
- Full descriptor oracle: 930 compared with the prior commit; 0 differences and one permitted
  unseeded optional-shape variance. Two targeted repeats produced the non-empty expected shape.
- Capabilities, compiler, Authoring reference, and scaffold-reference hashes are unchanged.
- Ruff and diff check pass. Full-package mypy reports only the two known missing optional Ray
  modules.

Service-backed descriptors not executed by the oracle remain unverified in this slice; the prior
OrbStack service gate remains the latest live MongoDB/PostgreSQL evidence.
