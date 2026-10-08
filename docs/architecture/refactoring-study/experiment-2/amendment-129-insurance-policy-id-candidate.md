# Amendment 129: insurance policy ID candidate ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign UUID candidate creation to `InsurancePolicyGenerator`. `InsurancePolicy`
retains its lazy cached ID property and delegates allocation to `BaseEntity`.

Preserve the five constructor RNG derivations and their order, `uuid4_from_random`
on the public RNG, policy/child stream ordering, collision handling without
redraw, and retry after errors.
