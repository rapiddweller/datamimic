# Amendment 151: AdministrationOffice founding year

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign founding-age ranges, sampling, and year calculation to
`AdministrationOfficeGenerator`. `AdministrationOffice` resolves the public
reference year before its type and retains the lazy cached property. Preserve
the existing `pick_founding_year(office_type)` method and its private clock/RNG
behavior; the model uses a new generator method with the resolved year. Preserve
range precedence, bounds, draw order, and failure/retry behavior.
