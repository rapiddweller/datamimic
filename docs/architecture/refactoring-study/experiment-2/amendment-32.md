# Amendment 32: close Runtime task interfaces

Date: 2026-09-28.

Use the shared subtask base types in `WhileTask`, publish the existing Runtime
construction helpers used across task families, and expose script execution
through the evaluation boundary. No execution policy or RNG behavior changes.

LOCAL VERIFIED: 1950 non-service tests passed (13 skipped), 55 focused QA
tests, Ruff, Mypy, recursive definition, Pylint import-cycle check, and
independent Terra review. ArchKeel reports 53 → 48 violations with no new
IDs or UNKNOWNs. The 930-XML oracle inventoried every input; comparison with
the prior slice differs only in two unseeded cases that also vary on
same-code repeat. Its frozen capabilities hash already drifted before this
slice, so the oracle command still exits 1.

CI-ONLY VERIFICATION: no remote run; full architecture validation remains
UNKNOWN/exit 2.
