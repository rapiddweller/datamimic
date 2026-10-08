# Amendment 92: Hospital capacity generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the existing bed-count and staff-count algorithms from cached `Hospital`
properties to `HospitalGenerator`. `Hospital` continues to resolve its cached
type and bed count, then delegates the corresponding calculation.

The CE ranges, fallback, RNG instance and call order, lazy caching, descriptors,
and output behavior remain unchanged. This aligns implementation ownership
with the existing Healthcare target; it adds no dependency or public grant.
