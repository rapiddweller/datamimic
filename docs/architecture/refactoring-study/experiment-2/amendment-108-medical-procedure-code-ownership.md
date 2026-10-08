# Amendment 108: Medical-procedure code ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move cached procedure-code generation to `MedicalProcedureGenerator`. Keep one
public RNG lookup followed by five sequential inclusive `randint(0, 9)` draws
and `P`-prefix formatting, including leading zeroes. Retain the model cache.
No ID, CPT, descriptor, or existing API behavior changes; adds the generator
operation.
