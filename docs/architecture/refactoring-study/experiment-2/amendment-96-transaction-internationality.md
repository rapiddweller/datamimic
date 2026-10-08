# Amendment 96: Transaction internationality generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the weighted `is_international` draw to `TransactionGenerator`. The model
property remains lazy and cached; the same shared RNG and weights are used, so
draw order and seeded behavior are unchanged. No existing API or descriptor
behavior changes; adds the generator operation.
