# Amendment 109: Medical-procedure CPT-code ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move cached CPT-code generation to `MedicalProcedureGenerator`. Preserve one
public RNG lookup followed by `randint(1, 9)` and four sequential
`randint(0, 9)` draws, formatting, and the model cache. No CPT semantics,
descriptor, or existing API behavior changes; adds the generator operation.
