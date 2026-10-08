# Amendment 104: Medical-procedure preventive-status ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the conditional preventive-status draw to `MedicalProcedureGenerator`,
passing the model's cached surgical flag. Preserve evaluation-before-draw
order, public RNG access, strict `< 0.05`/`< 0.3` thresholds, lazy cache, and
seeded behavior, including description-first property evaluation. No descriptor
or existing API behavior changes; adds the generator operation.
