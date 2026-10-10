# Amendment 143: AdministrationOffice jurisdiction ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign jurisdiction mapping and fallback formatting to
`AdministrationOfficeGenerator`. `AdministrationOffice` resolves type, city,
and state in order and keeps the lazy cached property. Preserve branch
precedence, selected-only formatting, bucket fallback, and failure behavior.
