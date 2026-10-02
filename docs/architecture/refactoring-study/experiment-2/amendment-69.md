# Amendment 69: finance serializer contracts

Date: 2026-09-29. Decision: Astra, with independent implementation and QA.

`BankAccount.to_dict()` and `Transaction.to_dict()` have fixed CE record shapes.
Finance owns their `BankAccountData` and `TransactionData` types. Models require
the Finance contracts component; the two types are public at the Finance,
Domains, and root component boundaries. No facade re-export is added.

The generic entity interface remains `Mapping[str, object]`. EE has the same
physical Finance owner but not yet the same typed serializers; that alignment
is still target work. Runtime keys, optional account omission, and datetime
values remain unchanged.
