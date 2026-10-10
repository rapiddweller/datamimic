# Step 82 — expose existing boundary records

Base: `275670f4d387dc07b01f3470a79748c8b9096181`.

- DSL API exports the existing `TimeSeriesNamespace` returned by `TimeSeriesConfig.at()`.
- Runtime API exports the existing `DemographicContext` used by `SetupContext` signatures.
- Identity and owner assertions reject duplicate records or accidental relocation. Definitions and execution stay unchanged.
- No descriptor, oracle, contract, allowance, budget or baseline changed.

Independent Luna implementation and QA; Astra reviewed the complete candidate. QA's frozen probe changes from two missing-export failures to five passes. The same time-series and seeded demographic behavior is preserved.

LOCAL VERIFIED on the isolated combined candidate: 1,542 unit passes, 11 skips, one xfail; 52 focused/frozen QA passes; Ruff and full-package MyPy (491 files). Pylint executable-cycle check, five recursive target tests and four inner target tests pass with explicit read-only Git context.

ArchKeel 0.8.1: 107 → 106 violations; counted UNKNOWN remains 157. The gate remains FAIL. This closes two missing facade names, not all public boundary typing; a frozen demographic record still contains mutable sampler/RNG references.

CI-ONLY VERIFICATION: base run `36801016773` finished FAILURE at the architecture gate (107 violations, 157 counted UNKNOWN). Other executed jobs succeeded; E2E/release skipped. This checkpoint's remote CI is pending push.

Full descriptor parity, pure Target/deep Diff report acceptance, merge and release remain open. SQL scripting compatibility stays separate and on hold pending ArchKeel #228.
