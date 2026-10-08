# Amendment 146: Administration office ID candidate

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the existing `ADM-` prefix and eight hexadecimal RNG draws to
`AdministrationOfficeGenerator`. `AdministrationOffice` retains the uniqueness
claim and lazy cached property. Preserve one public RNG lookup, the ordered
draws, candidate-before-claim behavior, and the existing registry collision,
failure, cache, and property-evaluation semantics. The generator does not retry
or enforce uniqueness.
