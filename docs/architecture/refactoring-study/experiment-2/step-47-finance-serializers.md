# Step 47: type the Finance serializers

[Amendment 69](amendment-69.md) declares the two existing Finance serialization
shapes at their owning boundaries. The account record has 11 required fields;
the transaction record has 15 required fields and an optional account record.
The generic entity base returns a read-only `Mapping` so concrete `TypedDict`
records fit without changing the runtime dictionaries.

The first dirty-worktree report (95 violations, 189 UNKNOWN positions) also
included unrelated unfinished changes. It is not the measurement for this
Finance slice. The isolated committed snapshot and CI must be measured
separately before claiming a delta.

LOCAL VERIFIED on the dirty candidate: 56 focused unit/architecture tests,
the Finance demo, full-package MyPy, and `git diff --check` passed. Independent
QA compared seeded serializer output with clean HEAD; it was byte-identical.
The pre-existing transaction type/detail mismatch remains separate. The full
descriptor oracle, service-backed tests, and CI are still unverified for this
slice. This step is not the final architecture gate.
