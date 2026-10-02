# Step 08B: remove cross-component logger ownership

## Change

- Replaced non-runtime imports of `engine.runtime.logging.logger` with the standard library named
  logger.
- Kept logger setup in runtime and fixed the single logger name to `DATAMIMIC`.
- Removed the unused, undocumented `Settings.DEFAULT_LOGGER` setting.

## Evidence

- ArchKeel violations: 887 -> 831; 56 baseline findings resolved; no new rule violation.
- Rules: `INTERFACES-ONLY` 502 -> 473 and `REQUIRES-COMPLETE` 64 -> 37.
- Cycle edges: unchanged at 177. The observed `interfaces -> runtime` edge is gone.
- Independent verification: 78 focused tests passed. All changed modules resolve the identical
  logger object; `MAIN` and worker handlers, levels, propagation, and formatters remain effective.
- Implementation sweep: 1,516 passed, 14 skipped, with the known probabilistic MedicalDevice
  status assertion failing once.
- Full package Ruff and diff check: pass.
- Full mypy reached 454 files and failed only on the two existing missing optional `ray` imports.
- Descriptor oracle: 930 compared, 0 differences, 2 optional-shape variances tolerated. Statuses
  and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `9feb858f903cf4a98b1fc3c40d3cba7ceeae07146756a85435bfdb571e840218`.

ArchKeel 0.6.0 reports 68 ordinary `logging.Logger` method calls as newly unresolved because its
resolver does not propagate the return type of `logging.getLogger(...)` into a module binding.
One explicit `logging.Logger.error(logger, ...)` probe resolved exactly one call; it was reverted.
Amendment 04 resets that measurement to 1,408 without changing any target permission. Removing
`DEFAULT_LOGGER` also removes an implicit environment override, but it had no tracked caller,
documentation, test, or public export contract. Service-backed tests remain unverified because the
configured Podman machine is unavailable.
