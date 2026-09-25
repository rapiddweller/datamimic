# Step 08C4: move statement execution decisions to runtime

## Change

- Moved count expression evaluation and range selection from DSL statements to runtime.
- Moved MongoDB-upsert target detection from `GenerateStatement` to the runtime source router.
- Removed the resulting DSL imports of runtime contexts and the MongoDB client.

## Evidence

- ArchKeel violations: 802 -> 791; `INTERFACES-ONLY` 456 -> 450 and
  `REQUIRES-COMPLETE` 29 -> 24. Cycle edges improve 177 -> 172.
- No new baseline fingerprint; unresolved calls remain 1,407.
- Implementation verification: 30 passed, 11 skipped. Independent verification: 68 passed,
  11 skipped.
- Ruff, targeted mypy, and diff check: pass.
- Seven affected count descriptors are byte-identical to Step 0: five captured and two expected
  errors. All four projection hashes also match.
- Full mypy checked 460 files and failed only on the two existing missing optional `ray` imports.

MongoDB end-to-end upsert remains unverified because the configured Podman machine is unavailable.
