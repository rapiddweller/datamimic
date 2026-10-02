# Amendment 28: name the domain interfaces actually used

Date: 2026-09-28. Independent Terra review of a fresh ArchKeel observation.

The Domain component graph is already directed downward. Its 128
`DOMAINS-INTERFACES` findings came from 20 imported dataset, RNG, demographic
and profile symbols missing from `DOMAINS-CORE` or `DOMAINS-SHARED.public`.
Publish those exact observed symbols in the inner Domain contract. Do not
publish their entire modules or add a forwarding facade.

The candidate ArchKeel report now shows 0 `DOMAINS-INTERFACES` findings, and
none of the new selectors is `interface.unused`. This is an interface widening
limited to current callers. It does not make external Python API promises.

LOCAL VERIFIED: contract JSON parses; candidate report 128 -> 0. No runtime
code or descriptor changed.

CI-ONLY VERIFICATION: no remote run; the full architecture gate remains red.
