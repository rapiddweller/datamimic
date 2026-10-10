# Amendment 123: transaction ID candidate ownership

Date: 2026-10-08. Decision: Astra-advised, coordinator-approved target clarification.

Assign generation of the 16-character transaction ID candidate to
`TransactionGenerator`. `Transaction` retains lazy caching and unique-ID claims.

Preserve the exact regex generator call and public RNG, lazy access, collision
allocation, serialized value and field order, and seeded outputs and RNG state.
