# Amendment 137: order-coupon-code ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign prefix selection, random-code generation, and concatenation to
`OrderGenerator`. `Order` retains the discount gate and caches `None` for
non-positive discounts.
