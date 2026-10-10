# Amendment 148: Order billing-address reuse decision

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the existing strict `rng.random() < 0.8` decision to
`OrderGenerator`. `Order` retains address construction, branch laziness,
relationship identity, and its cached billing property. Preserve one public RNG
lookup/draw before evaluating either address branch, the strict threshold,
failure/retry behavior, cache behavior after the shipping setter, and child
address RNG state.
