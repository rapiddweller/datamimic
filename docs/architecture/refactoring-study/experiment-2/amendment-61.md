# Amendment 61: align CE finance payload contracts with EE

Date: 2026-09-28. Decision: Astra.

The initial Step 20 implementation put the transaction result TypedDicts in
`transaction_generator.py` and named the aggregate `TransactionData`. That
ownership and name do not match EE. CE now owns `TransactionTypeData`,
`CurrencyData`, and `GeneratedTransactionData` in
`datamimic_ce.domains.finance.contracts`, matching
`datamimic_ee.domains.finance.contracts`. `CurrencyData.name` is optional:
the account-backed currency dictionary contains only `code` and `symbol`.

Declare the contracts as a finance leaf, with generators depending on that
leaf, and keep their public symbols at the contracts module. This is a type
and architecture correction only: dictionary construction, values, RNG calls
and order, `CurrencyAccount` runtime checking, and the
`object | None` input remain unchanged. No XML descriptor changes.

This amendment supersedes Step 20's local `TransactionData` proof and report.
Only verification recorded after this correction applies.

The pre-fix checker reports 124 `boundary_types` violations and 252 UNKNOWN
positions, versus 127 and 251 before the change. Its extra UNKNOWN is
`get_currency` return `name`: it does not unwrap `NotRequired[str]`. The
separate ArchKeel candidate fixes that limit; its CE report has 124 violations
and 251 UNKNOWN positions. The optional field matches the account currency
shape, and no exemption was added. `validate` retains 13 unrelated
`interface.unused` diagnostics.
