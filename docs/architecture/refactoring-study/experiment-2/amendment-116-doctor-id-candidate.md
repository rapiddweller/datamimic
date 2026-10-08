# Amendment 116: Doctor ID candidate ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move the eight ordered hexadecimal choices and `DOC-` formatting from
`Doctor.doctor_id` to `DoctorGenerator.generate_doctor_id_candidate()`. The
model keeps lazy access and caching; `BaseEntity` keeps optional unique-ID
allocation and collision handling.

Preserve CE's public-RNG accessor, draw order, unbound duplicate candidates,
claim order, seeded output and cache behavior. Do not change the separate
stable-UUID use case or introduce a generic identifier abstraction. No
descriptor or existing API behavior changes.
