# Step 08C27: isolated PostgreSQL descriptor comparison

`tests_ce/external_service_tests/test_rdbms/test_postgresql_local.xml` has the
same SHA-256 on frozen `a219163e` and target `6190932d`:
`a752ba2f6a43359fd9e7cc35e456cad1b208fba07570a38b2996ff9d38b3b4d7`.

An independent Luna verifier ran each revision once in a fresh PostgreSQL 18.6
container (image digest `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`).
The containers bound only to `127.0.0.1:32774` and `127.0.0.1:32775`, with
separate databases, users, and mode-0600 staged configs. Before any SQL, the
verifier asserted the checkout, container identity, resolved descriptor
endpoint, and empty `simple` schema. It never used the shared Platform or
field-service PostgreSQL containers.

Both descriptor runs passed. The verifier reported matching schema/constraint
and stable-row hashes. My separate read-only SQL query in each retained
container returned the same tuple:

```text
customer rows | user rows | product rows | unique customer IDs |
unique user IDs | unique emails | orphan/null customer refs |
bad customer constants | bad user constants
20|15|0|20|15|15|0|0|0
```

This proves outcome, schema, counts, and checked invariants for this unseeded
case; it does **not** prove every randomized column is byte-identical. After
QA, only the two experiment containers and their private stages were removed.
No repository fixture or shared service was changed. The orchestration was
inline and was not retained, limiting exact replay of the setup.
