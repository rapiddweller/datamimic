# Amendment 121: Medical procedure ID candidate ownership

Date: 2026-10-08. Decision: Astra-advised, coordinator-approved target clarification.

Move only candidate sampling and `PROC-` formatting from
`MedicalProcedure.procedure_id` to `MedicalProcedureGenerator`. The model keeps
lazy access and passes the candidate to `BaseEntity` for optional unique-ID
allocation and collision handling.

Preserve the public RNG accessor, eight ordered uppercase hexadecimal choices,
leading zeroes, cache and claim behavior, seeded output, and `to_dict()` order.
Keep the service schema, procedure codes, stable UUID behavior, and coupled
cached cost calculation unchanged.
