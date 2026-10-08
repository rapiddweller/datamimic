# Amendment 110: Doctor NPI generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move cached NPI generation to `DoctorGenerator`. Preserve one public RNG lookup,
ten sequential `randint(0, 9)` draws, leading zeroes, and the model cache. Keep
the existing shared/child RNG construction semantics; do not adopt EE's
field-keyed NPI strategy or add validation/check-digit behavior. No descriptor
or existing API behavior changes; adds the generator operation.
