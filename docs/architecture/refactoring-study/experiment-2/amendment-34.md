# Amendment 34: route Runtime selection through IO facade

Date: 2026-09-28.

Expose the existing generic selection operations through `io.api` and update
the Runtime imports. Selection policy and behavior are unchanged.

The root interface rule caught the old direct imports and an independent
package-level import probe. No second Python architecture checker was retained.
ArchKeel reports 40 → 37 violations with no new violation messages, but
67 → 71 UNKNOWN positions: the four new positions are `TypeVar`-generic facade
arguments/results, not a change to the source annotations. This remains gate debt.

LOCAL VERIFIED: 1960 non-service tests passed (13 skipped), 39 focused
architecture/source-selection tests, Ruff, Mypy,
Pylint import-cycle check, and independent Terra review. The 930-XML inventory
and status counts are unchanged; two unseeded outputs vary on same-code repeat.
The frozen capabilities hash already drifted, so the oracle command exits 1.

CI-ONLY VERIFICATION: no remote run. Full architecture validation remains
UNKNOWN/exit 2 (32 baseline-new findings).
