# Amendment 120: Patient ID candidate ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move only the eight hexadecimal choices and `PAT-` formatting from
`Patient.patient_id` to `PatientGenerator.generate_patient_id_candidate()`.
`Patient` retains lazy access and passes the candidate to `BaseEntity` for
optional unique allocation and collision handling.

Preserve one public RNG lookup, ordered choices, unbound duplicate candidates,
claim order, collision behavior, seeded output, and caching. Do not change the
separate stable-UUID use case, patient schema, descriptors, or output order.
