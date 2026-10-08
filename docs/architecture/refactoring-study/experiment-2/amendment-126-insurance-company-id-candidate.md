# Amendment 126: insurance company ID candidate ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign UUID candidate creation to `InsuranceCompanyGenerator`. `InsuranceCompany`
retains its lazy cached ID property and delegates allocation to `BaseEntity`.

Preserve `uuid4_from_random(self.rng)`, UUIDv4 version/variant bits and formatting,
the exact RNG state transition, collision handling without redraw, retry after
errors, and lazy company-data access.
