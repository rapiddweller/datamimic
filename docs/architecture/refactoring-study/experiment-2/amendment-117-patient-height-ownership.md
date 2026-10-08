# Amendment 117: Patient height ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move only the conditional height bounds, public-RNG draw, and rounding from
`Patient.height_cm` to `PatientGenerator.generate_height_cm(gender, age)`.
`Patient` must resolve gender, then age, before calling the generator, and keeps
the lazy property cache. Do not move demographic resolution, weight, BMI, or
their caches.

Preserve the current formulas and operation order, the `age < 18` boundary,
the exact `"Male"` branch and existing fallback for other values, one public
RNG lookup and one uniform draw. This is an ownership change only: no descriptor
or output change is intended.
