# Amendment 127: insurance product ID candidate ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign UUID candidate creation to `InsuranceProductGenerator`. `InsuranceProduct`
retains its lazy cached ID property and delegates allocation to `BaseEntity`.

Preserve `uuid4_from_random(self.rng)`, UUIDv4 formatting and RNG state, product
and coverage draw ordering, constructor-derived coverage RNG, collision handling
without redraw, and retry after errors.
