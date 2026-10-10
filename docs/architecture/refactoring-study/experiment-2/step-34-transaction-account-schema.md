# Step 34: make the Transaction account schema truthful

`Transaction.to_dict()` already emits the complete 11-field `BankAccount`
when an account is linked. `TRANSACTION_SCHEMA` declared only two nested
fields. The account group now reuses `BANK_ACCOUNT_SCHEMA.fields`; linked and
unlinked cases have focused schema checks. No generator, descriptor, runtime
serialization, or public Python return type changed.

The CE shape remains different from EE: CE omits an unlinked `account` and
emits the full linked account; EE emits `null` or a two-field summary. Copying
EE's shape here would break the frozen within-CE output contract. Edition
alignment needs a separate, explicit product decision.

The ArchKeel #209 measurement is unchanged at 123 `boundary_types`
violations, 93 new baseline positions, and 209 informational untyped import
positions. This slice fixes an inaccurate domain schema, not an ArchKeel
count. `datamimic reference entities Transaction` still abbreviates nested
children as `{…}`; making them inspectable is separate authoring work.

LOCAL VERIFIED: 58 focused architecture/API/unit tests, Ruff on the changed
files, full-package MyPy (489 files), Pylint cyclic-import gate, `git diff
--check`, and ArchKeel validation (still FAIL as above). CI-ONLY
VERIFICATION: not run for this provisional slice. Full DSL parity remains
open as recorded in [Step 31](step-31-descriptor-parity.md).
