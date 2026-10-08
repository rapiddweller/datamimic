# Step 33: isolated Postgres and Mongo descriptor parity

Compared frozen Step 0 (`a219163e`) with the current uncommitted CE tree
(`be769229`) in a private Docker Compose project, `ce-parity-xki0ub`.
Postgres 18.6 and MongoDB 7.0.12 had private volumes, an internal network, and
no published ports. Both checkouts and the parity probe were mounted read-only.
The descriptor and environment property files were byte-identical at both
revisions.

- Seeded `reference_postgresql.xml`: the captured database snapshot was
  byte-identical Alt/Neu (`01d543…`).
- Seeded `reference_mongodb.xml`: after clearing its three owned collections
  before **each** run, all captured products were byte-identical Alt/Neu
  (`1dc17f…`). The written documents were also byte-identical after excluding
  MongoDB-generated `_id` values (`308331…`).
- Without the explicit reset, MongoDB's `cleanup` product reads prior target
  documents. The first Alt/Neu snapshots differed in `tier`; an Alt/Alt repeat
  also differed. That comparison had unequal initial target state and cannot
  establish a code regression or same-state replay failure.
- The restricted Postgres/Mongo external-service suites passed on each
  checkout: 8 tests Alt, 8 tests Neu. The full two-module attempt had four
  failures for unavailable MSSQL/Oracle services; it was not a full service
  gate.

Raw captures are under `/private/tmp/ce-parity-XkI0uB/results/`. This proves
these two descriptors with controlled resources, not all 461 service-dependent
or otherwise unverified descriptors from [Step 31](step-31-descriptor-parity.md).
MongoDB's generated `_id` is deliberately excluded from the target snapshot;
its non-ID fields and relationships are compared exactly.

LOCAL VERIFIED: private-service health, two seeded descriptor captures,
Alt/Neu byte comparisons, same-edition control, and 8 restricted service tests
on each checkout. CI-ONLY VERIFICATION: not run for this provisional step.
