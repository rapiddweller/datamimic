# Amendment 36: declare model constraint extension boundary

The model registry owns element inventory and atomic extension lifecycle. It
consumes canonical constraint facts and coordinates rule registration/rollback
with element extensions. The constraints registry exposes per-tag mutation
operations through the internal SPI; the model registry owns atomicity. Keep
these operations out of `dsl.api`.

Evidence: the candidate ArchKeel report drops from 30 to 24 violations with
71 UNKNOWN unchanged; it reports no new violation or unused selector for this
boundary. Focused registration and unregistration rollback tests pass. All 930
descriptor inventory statuses are unchanged; the frozen capabilities hash still
drifts and one unseeded Memstore count varied on a same-code repeat.
