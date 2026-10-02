# Amendment 35: publish shared services through Domains API

Date: 2026-09-28.

Expose the five existing shared services through `domains.api` and route CE
examples/docs through that facade. The EE services have matching ownership but
remain under `shared.services`; this slice does not change EE. Checked EE
`dc7526592`: all five service files exist, and `domains/api.py` does not.

LOCAL VERIFIED: 1961 non-service tests passed (13 skipped), seven focused
architecture/API tests, Ruff, Mypy, Pylint import-cycle check, and independent
Terra review. ArchKeel reports 37 → 30 violations, no new violation messages,
and 71 UNKNOWNs unchanged. The 930-XML inventory and status counts are unchanged;
one unseeded Memstore count also varies on same-code repeat. The frozen
capabilities hash already drifted, so the oracle command exits 1.

CI-ONLY VERIFICATION: no remote run. Full architecture validation remains
UNKNOWN/exit 2 (25 baseline-new findings).
