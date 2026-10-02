# Step 08C2: derive Authoring generator capabilities

## Change

- Moved `SequenceTableGenerator` from domains to runtime without changing its logic.
- Replaced Authoring's package scan with typed DSL, domain, and runtime capability APIs.
- Activated the DSL and runtime facade type rules.

## Evidence

- ArchKeel violations: 817 -> 804; `INTERFACES-ONLY` 464 -> 457,
  `REQUIRES-COMPLETE` 33 -> 30, and `NO-MAGIC-CONTROL-FLOW` 311 -> 310.
- Cycle edges remain 177; unresolved calls improve 1,408 -> 1,407; typing positions improve
  460 -> 458.
- `DSL-API-TYPES`, `DOMAIN-API-TYPES`, and `RUNTIME-API-TYPES`: pass with every signature
  position decided.
- Implementation verification: 94 passed, 11 skipped. Independent verification: 61 passed.
- Full unit suite: 1,117 passed, 11 skipped.
- Full package Ruff and diff check: pass.
- Full mypy reached 459 files and failed only on the two existing missing optional `ray` imports.
- Descriptor oracle: 930 compared, 0 differences, 0 optional variances. Statuses and all four
  canonical projection hashes match Step 0. Snapshot SHA-256:
  `6b85ea1b383c15eab751d1c10b0ddd4a3b968417c5fbb594c4600169c943f20e`.

The single new baseline fingerprint is the existing `hasattr` construct relocated with
`SequenceTableGenerator`; 13 old fingerprints resolve. Service-backed sequence tests remain
unverified because the configured Podman machine is unavailable.
