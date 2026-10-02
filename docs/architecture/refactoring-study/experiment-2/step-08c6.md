# Step 08C6: remove include execution from DSL statements

## Change

- Removed property-file loading from `IncludeStatement`.
- Kept static property includes in the parser, where they affect later sibling attributes.
- Kept dynamic includes deferred and XML includes unchanged.

## Evidence

- ArchKeel violations: 785 -> 784; `REQUIRES-COMPLETE` 21 -> 20. No new baseline
  fingerprint; unresolved calls remain 1,404.
- Implementation and independent verification: 4 passed each.
- Ruff, targeted mypy, and diff check: pass.
- Six affected include descriptors are byte-identical to Step 0: four captured and two
  unrunnable. All four projection hashes also match.

The remaining parser-level file and environment dependencies are deliberately deferred to the
next slice. Service-backed tests remain unverified because the configured Podman machine is
unavailable.
