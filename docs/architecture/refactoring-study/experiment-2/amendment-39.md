# Amendment 39: remove unused facade aliases

Remove the unused `io.api.resolve_target_entity_from_metadata` and
`dsl.api.serialize_source_capability` re-exports. Keep both owner operations;
callers use their owning modules. This is an intentional Python import-path
break for 5.0 and does not change DSL results.

Evidence: candidate ArchKeel violations fall from 20 to 18 with 71 UNKNOWN
unchanged and no new violation. The non-service suite passes (1969 tests,
13 skips); Ruff, MyPy, cycle and recursive target checks pass. The 930
descriptor statuses and seeded outputs match S3G19. Two unseeded observations
vary in the same known dynamic Memstore count and Boolean-conditional demo
field; both were reproduced on identical code. The frozen capabilities hash
still differs from step 0.
