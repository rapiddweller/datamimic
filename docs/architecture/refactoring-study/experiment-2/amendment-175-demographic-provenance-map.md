# Amendment 175 — exact demographic provenance map

2026-10-09. Base `c6cf1723997ba176d0403ab3bc8ab56fa99b6b32`.

Allow only `datamimic_ce.domains.api.DemographicSampler.provenance_descriptor`
at `return`, empty `field_path`, exact `dict[str, str]` in `DOMAIN-API-TYPES`.
Its fresh ordinary dict contains recorded normalized resource paths and digest
strings. Digests include path spelling and bytes/missing marker. This is not fresh
filesystem hashing, exact active-resource completeness or stale-path pruning.
Dynamic path keys cannot be fixed record fields; no DTO, wrapper or source change.

All other rules, allowances, owners, dependency grants and source/test/baseline bytes
remain unchanged. [Amendment 77](amendment-77.md) supplies precedent.
Only this amended rule changes `decided_by` from architect to agent: attribution
is rule-wide because the schema has no per-position label. The delegated allowance
does not claim human confirmation or revoke retained policy.

LOCAL VERIFIED: independent source/caller review, exact matcher one positive/eight
negatives, Ruff/MyPy (488 files), definition 13 PASS and published 1.0.0 report.
Only `VIO-95f28d4d056ed4a5` disappears: global FAIL86 / 200 measured UNKNOWN /
254 canonical UNKNOWN. All remaining finding/UNKNOWN records, source digest and
184 existing typing records are exact. The full projection retains 151 components,
25 levels and zero gaps; ownership and dependency grants are unchanged.
This exact type allowance is the sole policy change.
Baseline validation exits 2: 55 new, zero resolved, 19 diagnostics and 58 failures.
Unamended against-base exits 2 with the same diagnostics and 60 failures, including
two widenings (`allowed_positions`, `decided_by`); amendment status stays null.
The first against invocation omitted the required baseline and failed before
observation; its raw result is retained separately. No writer or baseline change.
Step152 extraction HOLD and machine binding OPEN/#415 remain.
CI-ONLY VERIFICATION: no new-head claim. External consumers, broader maps,
private-state validation and whole-target semantic acceptance remain UNKNOWN.
