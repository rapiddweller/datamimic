# Amendment 114: Patient medical-record-number ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

The frozen target prohibited `Patient` from generating values directly but did
not name an owner for medical-record-number generation. Assign sampling and
`MRN-########` formatting to `PatientGenerator.generate_medical_record_number()`.
`Patient` keeps lazy property access and its cache. MRNs remain non-unique;
`BaseEntity`/`IdentifierRegistry` are not involved.

Preserve the single public-RNG lookup, eight ordered uppercase-hex choices,
leading zeroes, seeded access-order behavior, and duplicate values across
patients. No descriptor or existing API behavior changes.
