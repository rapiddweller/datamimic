# Amendment 115: Patient SSN ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move the nine ordered digit draws and `###-##-####` formatting from
`Patient.ssn` to `PatientGenerator.generate_ssn()`. `Patient` keeps lazy access
and its cache. Preserve CE's current public-RNG stream; do not copy the EE's
field-keyed RNG behavior, validation, filtering, or uniqueness policy.

The EE already delegates `Patient.ssn` to `PatientGenerator.generate_ssn()`.
This aligns ownership only: the CE must keep its existing outputs, draw order,
and construction-time RNG state. No descriptor or existing API behavior changes.
