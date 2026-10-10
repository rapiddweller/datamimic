# Amendment 107: Hospital teaching-status ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the teaching-status decision to `HospitalGenerator`. `Teaching` returns
`True` without accessing the public RNG; `General` uses `<0.3`, and every other
type uses `<0.1`. Resolve the cached type first and retain the model cache and
public RNG override behavior. No descriptor or existing API behavior changes;
adds the generator operation.
