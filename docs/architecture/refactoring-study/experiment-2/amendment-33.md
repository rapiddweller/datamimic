# Amendment 33: narrow IO facade and declare shared operations

Date: 2026-09-28.

Remove unused concrete exporter re-exports from `io.api`, expose the existing
JSON shape guards by their operation names, and declare the registry's Memstore
dependency. Behavior is unchanged.

LOCAL VERIFIED: 1960 non-service tests passed (13 skipped); 18 targeted
architecture/JSON tests, Ruff, Mypy, Pylint import-cycle check, and independent
Terra review passed. ArchKeel reports 48 → 40 violations, with no new violation
messages; 67 UNKNOWNs remain. The 930-XML inventory and status counts are
unchanged. One unseeded optional condition field differs from the prior run and
also varies on same-code repeat. The frozen capabilities hash had already drifted,
so the oracle command exits 1.

CI-ONLY VERIFICATION: no remote run. Full architecture validation remains
UNKNOWN/exit 2 (35 baseline-new findings).
