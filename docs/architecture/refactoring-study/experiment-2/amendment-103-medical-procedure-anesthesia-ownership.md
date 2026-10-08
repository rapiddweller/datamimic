# Amendment 103: Medical-procedure anesthesia ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the conditional anesthesia draw to `MedicalProcedureGenerator`, passing
the model's cached surgical flag. Preserve its evaluation-before-draw order,
public RNG accessor, strict `< 0.9`/`< 0.2` thresholds, lazy one-draw cache,
and seeded behavior. No descriptor or existing API behavior changes; adds the
generator operation.
