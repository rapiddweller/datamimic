# Amendment 112: Medical-device ID candidate generation

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move only the eight ordered public-RNG digit draws and `DEV-########`
formatting to `MedicalDeviceGenerator.generate_device_id_candidate()`. Keep
`MedicalDevice.device_id` responsible for one `_claim_identifier()` call and
cache its returned value. `BaseEntity`/`IdentifierRegistry` remain responsible
for optional uniqueness; the generator neither claims nor retries identifiers.

Preserve unbound duplicate candidates, deterministic registry collision
resolution without extra RNG draws, public RNG accessor ordering, and
per-model caching. No descriptor or existing API behavior changes.
