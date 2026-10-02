# Step 08C30: MongoDB pagination edge and decimal parity

Two more byte-unchanged descriptors were compared on frozen `a219163e` and
target `6190932d` in four separate, disposable MongoDB 7.0.12 containers.
Each had a unique database, loopback-only port, and mode-0600 staged config.
The verifier checked imported revision, XML hash, resolved endpoint, container
identity, and empty collection before execution. No shared MongoDB was used.

| XML path under `tests_ce/external_service_tests/test_mongodb/` | XML SHA-256 | Result |
|---|---|---|
| `test_mongodb_pagination_edge.xml` | `bd311fecaa0c38dafb526a08459b0377f52bc13b35396b616ec0a24439656441` | Unseeded; both runs captured unique IDs 1..17 and the same normalized SHA-256 `26b821bc3f48c9f5cfbcb963203e375c12ec411443687a5546cac304a9c9d21e`. |
| `test_mongodb_decimal.xml` | `722b333ef3002bffdea5e0b9123b49798aec3cb328de0d8fd2351404ea891533` | Seeded (`rngSeed=11`); captured rows and aggregate `245.31` match exactly, SHA-256 `045bf7d072259c246d9ffca558642ce8a7c1675fe7aef68ded1345910f89e6f9`. |

The image digest was
`sha256:ae1cf99fa7bfb007db8416ad4f3980c46054d949fa55d28e6d301a813fee6c06`.
My separate authenticated read-only query returned zero remaining documents
in each of the four dedicated collections. After QA, only these four own
containers and stages were approved for removal. No repository fixture or
shared service was changed. The runner was inline and not retained.
