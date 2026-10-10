# Amendment 65: declare BankAccount API types

Date: 2026-09-29. Decision: Astra.

`BankAccount.bank_data` returns `Bank`, and `BankAccount.__init__` accepts
`BankAccountGenerator`. Add those exact type symbols to root `COMP-DOMAINS`; nested
`DOMAINS-FINANCE` already owns both. This corrects missing declarations for the concrete
model API; it does not add convenience exports, runtime code, or registry changes.
The architecture gate checks the ownership declarations.
