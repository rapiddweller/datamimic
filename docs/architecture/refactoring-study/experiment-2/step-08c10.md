# Step 08C10: finish DSL facade routing

## Change

- Routed every IO and domain dependency on DSL types and constants through `engine.dsl.api` or
  `engine.dsl.contracts`.
- Changed imports only. The DSL facade required no additional export.

## Evidence

- ArchKeel violations: 434 -> 400; 33 baseline fingerprints covering 34 imports resolved and 0
  added.
- IO/domain -> DSL interface violations: 34 -> 0. Cycle edges remain 171.
- Implementation-focused matrix: 419 passed. Independent focused matrix: 399 passed.
- Fresh-process import-order checks passed and all 19 moved symbols preserve object identity.
- Full descriptor oracle repeat: 930 compared with the prior commit; 0 differences and one
  permitted unseeded optional-shape variance. All four Authoring projection hashes are unchanged.
- One first-run capture result was lost under parallel load despite successful execution logs; two
  isolated serial repeats and the second full run captured the baseline-equivalent 100 rows.
- Ruff and diff check pass. Full-package mypy reports only the two known missing optional Ray
  modules.

Service-backed descriptors not executed by the oracle remain unverified in this slice; the prior
OrbStack service gate remains the latest live MongoDB/PostgreSQL evidence.
