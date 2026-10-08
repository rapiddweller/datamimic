# Amendment 90: Bank value generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

The Finance target already assigns value generation to generators. Bank's BIC,
BIN, and customer-service phone were still generated in cached model properties;
move those existing operations to `BankGenerator` while `Bank` keeps lazy cached
access. Clarify the responsibilities of `BankGenerator`, `Bank`, and the Finance
`generators` component to match that ownership.

No ownership selector, dependency permission, public grant, rule, budget, RNG
behavior, descriptor, or EE algorithm changes. This receipt covers only the
three responsibility statements above, not other ArchKeel widenings in the
working tree.
