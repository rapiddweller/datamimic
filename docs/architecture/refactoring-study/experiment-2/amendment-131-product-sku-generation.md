# Amendment 131: product SKU generation ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign SKU formatting and numeric-segment generation to `ProductGenerator`.
`Product` retains its lazy cached property and resolves brand before category.

Preserve the six-digit regex, public RNG state, output formatting, and retry
after generation errors.
