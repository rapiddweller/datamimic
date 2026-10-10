# Amendment 124: address house-number ownership

Date: 2026-10-08. Decision: Astra-advised, coordinator-approved target clarification.

Assign house-number sampling and formatting to `AddressGenerator`. `Address`
retains its lazy cache and serialization.

Preserve one public RNG lookup, the `randint(1, 9999)` then weighted `choices`
order and arguments, suffix formatting, per-instance caches, failure retry,
and fixed-country/region-group outputs and RNG states. Do not change country
resolution timing or use a child RNG.
