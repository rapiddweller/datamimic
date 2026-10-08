# Amendment 128: police officer ID candidate ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign officer-ID candidate sampling and formatting to `PoliceOfficerGenerator`.
`PoliceOfficer` retains its lazy cached property and delegates unique allocation
to `BaseEntity`.

Preserve one public generator RNG access, eight ordered uppercase-hex choices,
`OFF-` formatting, cache and retry behavior, duplicate unbound candidates, and
collision allocation without redraw.
