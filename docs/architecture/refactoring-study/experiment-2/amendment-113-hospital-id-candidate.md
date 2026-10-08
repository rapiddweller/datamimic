# Amendment 113: Hospital ID candidate generation

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move only the eight ordered public-RNG hex choices and `HOSP-########`
formatting to `HospitalGenerator.generate_hospital_id_candidate()`. Keep
`Hospital.hospital_id` responsible for one `_claim_identifier()` call and cache
its returned value. `BaseEntity`/`IdentifierRegistry` retain unique allocation;
the generator neither claims nor retries IDs.

Preserve unbound duplicate candidates, deterministic registry collision
resolution without extra RNG draws, and the lazy website fallback's use of the
claimed cached ID. A long hospital name must not force ID generation. No
descriptor or existing API behavior changes.
