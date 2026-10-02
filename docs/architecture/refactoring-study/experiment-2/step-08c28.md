# Step 08C28: isolated MongoDB descriptor comparison

`tests_ce/external_service_tests/test_mongodb/test_mongodb_pagination_happy.xml`
has the same SHA-256 on frozen `a219163e` and target `6190932d`:
`b364e8017cd4099124b4810cf7fdd52b32ceb2cec5dcb712f5b004b0595f870a`.

An independent Luna verifier ran each revision once in a fresh MongoDB
container (image digest `sha256:ae1cf99fa7bfb007db8416ad4f3980c46054d949fa55d28e6d301a813fee6c06`).
The containers bound only to `127.0.0.1:32768` and `127.0.0.1:32769`, with
separate databases and mode-0600 staged configs. Before execution, the
verifier asserted the checkout, container identity, resolved credentials and
endpoint, and empty collection. The shared Platform MongoDB was not used.

Both runs passed, captured IDs `1..20`, and produced the same captured-row
SHA-256 `4b4920b3a38d1b3d24a3904b1361dadb6c3645d2149497b86f389eaeca76c8b4`.
My separate authenticated read-only query confirmed that the
`mongo_pagination_happy` collection contained zero documents after each run.
This is exact captured-row parity for this case, but it is not a claim that
all unseeded runs always replay exactly. After QA, only the two experiment
containers and their private stages were removed. No repository fixture or
shared service was changed. The orchestration was inline and was not retained.
