# Amendment 101: Hospital founding-year ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the lazy founding-year draw to `HospitalGenerator`. Preserve the accessor
order (`reference_now` once, then public `rng`), inclusive year bounds, and
cached model property. This preserves seeded behavior and subclass overrides.
No descriptor or existing API behavior changes; adds the generator operation.
