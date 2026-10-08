# Step 32: declare two Finance boundary types

The `BankAccount` API already exposes `Bank` and `BankAccountGenerator` in its
annotations. [Amendment 65](amendment-65.md) declares those exact symbols at the
root Domains boundary; the nested Finance boundary already declared them. No
Python code or descriptor changed in this slice.

With the same merged ArchKeel #209 analyzer, the current dirty tree's report
decreased from 125 to 123 violations; `DOMAIN-API-TYPES` decreased from 36 to
34. The frozen baseline still reports 93 new positions because it predates the
analyzer's expanded facade measurement. This is not a passing architecture gate.

LOCAL VERIFIED: 9 focused architecture tests, Ruff, full-package MyPy, and
`git diff --check` passed. The report read and parsed all 489 Python files.
CI-ONLY VERIFICATION: not run for this CE slice. Full descriptor and service
parity remain open, as recorded in [Step 31](step-31-descriptor-parity.md).
