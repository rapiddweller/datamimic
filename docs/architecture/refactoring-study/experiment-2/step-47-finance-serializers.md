# Step 47: type the Finance serializers

[Amendment 69](amendment-69.md) declares the two existing Finance serialization
shapes at their owning boundaries. The account record has 11 required fields;
the transaction record has 15 required fields and an optional account record.
The generic entity base returns a read-only `Mapping` so concrete `TypedDict`
records fit without changing the runtime dictionaries.

The first dirty-worktree report (95 violations, 189 UNKNOWN positions) also
included unrelated unfinished changes and is not comparable. On isolated
commit `4e484d9d`, the pinned ArchKeel checker reports 108 violations versus
115 on the previous clean PR commit, 176 UNKNOWN positions unchanged, and
86 baseline-new versus 92. It parsed all 490 files. The architecture gate
still fails; these are residual findings, not a waiver.

LOCAL VERIFIED on the isolated commit: 13 focused unit/architecture tests,
five target-definition tests, Ruff, full-package MyPy (490 files), and Pylint
cyclic-import check passed. The Finance contracts loaded under Python 3.10 with
the declared `typing-extensions` dependency. Independent QA compared seeded
serializer output with clean HEAD; it was byte-identical. The pre-existing
transaction type/detail mismatch remains separate. The full descriptor oracle,
service-backed tests, and CI are not yet rerun for this commit. This step is
not the final architecture gate.
