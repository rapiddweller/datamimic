# Amendment 149: Order IDs

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign order-ID candidate and user-ID generation to `OrderGenerator`, reusing
`PrefixedIdGenerator` with the existing prefixes, pattern, separator, and public
RNG. `Order` retains the order-ID claim and both lazy caches. User IDs remain
unclaimed; preserve output, access order, RNG state, and failure/retry behavior.
