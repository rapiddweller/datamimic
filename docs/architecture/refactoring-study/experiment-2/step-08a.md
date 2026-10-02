# Step 08A: centralize packaged domain dataset IO

## Change

- Routed 29 domain dataset readers through `domains.utils.dataset_loader`.
- Added `engine.io.dataset_api`, exposing only file loading and caching to domains.
- Corrected the target so `domains` may require `io` only through that facet; direct pagination
  and database imports remain violations.
- Replaced one transaction CSV cast with its real `tuple[str, ...]` type.

## Evidence

- ArchKeel violations: 922 -> 887; baseline fingerprints: 869 -> 839; no new baseline finding.
- Rules: `REQUIRES-COMPLETE` 98 -> 64 and `NO-MAGIC-CONTROL-FLOW` 313 -> 312.
- Cycle edges: unchanged at 177. The 8 remaining `domains -> io` violations are the existing
  pagination and database paths outside `dataset_api`.
- Implementation sweep: 579 passed, 1 skipped, with one known probabilistic MedicalDevice
  inequality failure. The same unseeded assertion failed on an isolated retry.
- Independent verification: 288 focused tests passed after deselecting one unrelated random
  float-boundary assertion that passed alone.
- Full unit suite: 1,117 passed, 11 skipped.
- Focused transaction API suite: 8 passed.
- Full package Ruff: pass.
- Full mypy reached 454 files and failed only on the two existing missing optional `ray` imports.
- Pinned ArchKeel 0.6.0 baseline and amendment validation: pass with no new finding; target rules
  remain `FAIL` while 887 baseline violations remain.
- Descriptor oracle: 930 compared, 0 differences, 0 optional-shape variances. Statuses and all
  four canonical projection hashes match Step 0. Snapshot SHA-256:
  `903a7ad8af9af3dedb49282be8018ced14aa59511d8d8d7973b999f492454aba`.

Required Police dataset columns now fail immediately with `KeyError` instead of propagating
`None`; all shipped datasets satisfy that contract. The new facet still re-exports classes rather
than typed functions, so its final function boundary and `boundary_types` activation remain target
work. Service-backed tests remain unverified because the configured Podman machine is unavailable.
