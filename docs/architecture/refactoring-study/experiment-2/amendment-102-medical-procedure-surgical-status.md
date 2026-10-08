# Amendment 102: Medical-procedure surgical-status ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the lazy surgical-status draw to `MedicalProcedureGenerator`. Preserve the
public RNG accessor, strict `< 0.3` threshold, one draw, and cached model
property. This keeps access-order and seeded behavior unchanged. No descriptor
or existing API behavior changes; adds the generator operation.
