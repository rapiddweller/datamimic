# Amendment 27: remove two component cycles

Date: 2026-09-28. Astra decided the ownership before code moved.

`PhoneNumberGenerator` belongs to `domains/shared/generators`: it uses country and
city generators. The builtin DSL inventory belongs to the existing
`domains/registry/generators.py`, not to literal generators. Moving the phone
module alone would leave the registry's reverse edge and the cycle in place.
`engine/runtime/process_titles.py` belongs to Runtime Logging, not Lifecycle:
the worker needs it without depending on run orchestration. Both moved modules
are byte-identical; the worker import stays local. No old-path shims or DSL
descriptor changes are allowed.

The contract now declares `model.validation -> constraints` and the three
Python entry classes as external `public_api`, not unused internal interfaces.
It also names the exact Authoring spec symbols used across its components.
`EntityValue` remains IO-owned: Domains already depends on IO file readers,
and moving the nominal ABC into Domains would create a root cycle. The `through`
selector now names the actual `io.contracts` module, which ArchKeel can match.

These are target corrections, not acceptance. The remaining rule violations
and external-service parity are tracked separately; the baseline is not widened.
