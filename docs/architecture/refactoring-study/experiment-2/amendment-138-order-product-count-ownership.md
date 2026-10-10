# Amendment 138: order product-count ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the inclusive 1–10 product-count draw to `OrderGenerator`. `Order`
retains per-item `Product` construction and generator lookup, list ordering, and
the lazy cached property and setter.
