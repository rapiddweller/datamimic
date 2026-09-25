# Step 08C3: move transition rules to the DSL

## Change

- Moved the state-transition tuple type to the DSL contract.
- Kept the former domain `Rule` name as a compatibility alias.
- Removed the last DSL import from domains.

## Evidence

- ArchKeel violations: 804 -> 802; `INTERFACES-ONLY` 457 -> 456 and
  `REQUIRES-COMPLETE` 30 -> 29. No new baseline fingerprint.
- The observed component graph no longer contains `dsl -> domains`.
- Implementation verification: 12 passed. Independent verification: 10 passed.
- Broader state-transition and Authoring suite: 439 passed.
- Ruff, targeted mypy, and diff check: pass.
- The five affected state-machine and transition descriptors are byte-identical to Step 0,
  including the expected-error case. All four projection hashes also match.

Full mypy checked 459 files and failed only on the two existing missing optional `ray` imports.
Service-backed tests remain unverified because the configured Podman machine is unavailable.
