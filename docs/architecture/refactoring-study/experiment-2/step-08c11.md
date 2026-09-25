# Step 08C11: establish the domain facade

## Change

- Expanded `domains.api` from the initial generator facet to the exact cross-component domain
  vocabulary already used by runtime, Authoring, interfaces, and shipped resource scripts.
- Routed every external domain import through that facade; no wrapper or replacement type was
  added.

## Evidence

- ArchKeel violations: 400 -> 347; all 53 domain-internal crossing violations resolved and 0
  added.
- Cross-component imports from domain internals: 53 -> 0. Cycle edges remain 171.
- `domains.api`: 43 unique exports; 41 preserve source-object identity and 2 are its existing
  capability iterators.
- Implementation matrix: 779 passed, 11 skipped; 2 resource demos passed. Independent matrix: 414
  passed; 4 shipped demo integrations passed.
- Full descriptor oracle: 930 compared with the prior commit; 0 differences and 2 permitted
  unseeded optional-shape variances. All four Authoring projection hashes are unchanged.
- Ruff and diff check pass. Full-package mypy reports only the two known missing optional Ray
  modules.

Service-backed descriptors not executed by the oracle remain unverified in this slice; the prior
OrbStack service gate remains the latest live MongoDB/PostgreSQL evidence.
