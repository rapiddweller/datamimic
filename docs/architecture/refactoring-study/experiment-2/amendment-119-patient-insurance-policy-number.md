# Amendment 119: Patient insurance policy number ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Move only insurance-policy-number sampling and formatting from
`Patient.insurance_policy_number` to
`PatientGenerator.generate_insurance_policy_number()`. `Patient` retains its
lazy cache; provider resolution and identifier allocation are not involved.

Preserve one public RNG lookup, three ordered uppercase-letter choices followed
by eight digit draws, leading zeroes, and `AAA-12345678` formatting. Duplicate
values remain allowed. This changes ownership only; descriptors, RNG stream,
and public behavior must remain unchanged.
