# Amendment 98: Medical-procedure duration ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the existing duration draw to `MedicalProcedureGenerator`, passing the
model's cached surgical flag. The exact ranges, lazy timing, property cache,
cost evaluation order, and seeded behavior remain unchanged. No descriptor or
existing API behavior changes; adds the generator operation.
