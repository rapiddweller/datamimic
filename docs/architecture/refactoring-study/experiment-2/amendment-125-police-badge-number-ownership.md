# Amendment 125: police badge-number ownership

Date: 2026-10-08. Decision: Astra-advised, coordinator-approved target clarification.

Assign badge-number sampling and formatting to `PoliceOfficerGenerator`.
`PoliceOfficer` retains its cached property.

Preserve the public generator accessor, one RNG lookup, four ordered
`randint(0, 9)` draws, leading zeroes, duplicate values, per-officer caching,
failure retry, and seeded badge/officer-ID access-order behavior.
