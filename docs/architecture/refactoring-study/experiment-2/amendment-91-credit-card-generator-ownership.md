# Amendment 91: Credit-card credential generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move card-number and security-code generation from cached `CreditCard` properties
to `CreditCardGenerator`; the model retains lazy cached access. Move the declared
Finance `models -> algorithms` dependency to `generators -> algorithms`, where
the Luhn check-digit primitive is now used.

The existing CE algorithms, RNG draw order, cached card specification, separate
CVV/CVC draws, edge-case behavior, descriptors, and cross-edition output remain
unchanged. No new public grant or dependency is added; only the owner of the
existing algorithms dependency changes.
