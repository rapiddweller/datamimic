# Amendment 106: Hospital emergency-services ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the lazy emergency-status draw to `HospitalGenerator`. Resolve the model's
cached type before using the public RNG; preserve `<0.3` for `Specialty` and
`<0.9` for every other type, including unknown strings. Keep the per-model
cache and seeded draw order. No descriptor or existing API behavior changes;
adds the generator operation.
