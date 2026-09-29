# Step 59: narrow IO's public facade

Commit `07fd44b4` removes five unused implementation re-exports from
`io.api` and the parent IO contract. Their owner modules remain. This is an
undocumented Python import-path contraction, not a typing fix; see
[Amendment 71](amendment-71.md).

LOCAL VERIFIED on an isolated checkout: 1,482 unit tests passed (11 skipped,
1 xfailed); six focused architecture tests and five recursive target-definition
tests passed. Ruff, full-package MyPy (491 files), the pinned Pylint cycle
check and `git diff --check` passed. ArchKeel observed 491/491 files:
violations 96 → 91, UNKNOWN positions 176 → 168, baseline-new 74 → 69.
`observation_complete` passes; `declared_rules` still fails.

The full 930-descriptor equivalence gate and service-backed suites were not
rerun for this slice. CI has not run for this commit. The previous pushed
checkpoint passed build, wheel smokes, determinism, unit, integration,
functional, API, factory, external-service, Ruff and MyPy; its architecture
gate failed on remaining target violations.
