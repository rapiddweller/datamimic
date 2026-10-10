# Amendment 118: Patient weight ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move only BMI sampling, weight calculation, variation, and rounding from
`Patient.weight_kg` to `PatientGenerator.generate_weight_kg(age, height_cm)`.
`Patient` resolves and caches age and height first, then delegates; its lazy
weight cache and the BMI property remain in the model.

Preserve the `age < 18` BMI bounds, arithmetic and draw order, one public RNG
lookup for the weight calculation, use of that same RNG for both draws, and
one-decimal rounding. Do not add clamping or validation. This changes ownership
only; descriptors, seeded output, and public behavior must remain unchanged.
