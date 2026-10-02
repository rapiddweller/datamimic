# Amendment 40: publish IO exporter boundary types

`io.api` re-exports the Memstore, TestResultExporter and UnifiedBufferedExporter
types already used by Runtime. The exporter contract now declares those types;
`ExporterContext` is published beside `create_exporter_list` so callers can name
its parameter type. No behavior changes.

LOCAL VERIFIED: 1969 non-service tests passed (13 skipped); Ruff, full Mypy,
Pylint import-cycle check, recursive target checks and independent Luna/Terra
review passed. Candidate ArchKeel reports 18 → 14 violations, with no new
findings or UNKNOWNs. The 930-XML inventory and status counts are unchanged;
two unseeded descriptors vary on same-code repeats. The frozen capabilities
hash still differs, so the oracle command exits 1. Full architecture
validation remains UNKNOWN/exit 2 with existing graph and baseline drift.

CI-ONLY VERIFICATION: no remote run.
