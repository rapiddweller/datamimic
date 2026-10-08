# Amendment 105: Medical-procedure diagnostic-status ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the conditional diagnostic-status draw to `MedicalProcedureGenerator`,
passing the model's cached surgical flag. Preserve the public RNG accessor,
strict `< 0.2`/`< 0.7` thresholds, lazy cache, and seeded behavior. `name`
continues evaluating its diagnostic argument even for surgical naming; no
descriptor or existing API behavior changes, and no other evaluation order is
altered.
