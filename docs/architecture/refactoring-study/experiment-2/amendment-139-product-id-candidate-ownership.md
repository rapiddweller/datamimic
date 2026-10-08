# Amendment 139: product ID candidate ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign construction and generation of the product ID candidate to
`ProductGenerator`. `Product` still claims the candidate through
`_claim_identifier` and retains its lazy cached property.
