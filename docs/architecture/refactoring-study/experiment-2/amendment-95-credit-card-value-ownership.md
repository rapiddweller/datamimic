# Amendment 95: Credit-card value generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the existing `is_active`, `credit_limit`, and `current_balance` draws from
`CreditCard` to `CreditCardGenerator`. The model properties remain lazy and
cached; generation uses the same injected RNG and exact expressions.

Seeded values, access-order effects, per-model property caches, descriptors,
and the existing behavior where current balance may exceed credit limit remain
unchanged. This records ownership already implied by the Finance target; it adds
no dependency or public grant. EE still owns these draws on its `CreditCard`
model; track that ownership alignment separately. Do not copy EE's field-keyed
RNG policy into CE.
