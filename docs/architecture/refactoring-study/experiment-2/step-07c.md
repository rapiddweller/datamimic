# Step 07C: remove the root utility package

## Change

- Moved cumulative sampling to `domains.common` and source selection to `engine.runtime.sources`.
- Replaced the live `StringUtil` and `ObjectUtil` paths with small owner-local functions.
- Deleted the unused `DomainClassUtil` API and routed entity lookup only through the domain registry.
- Rejected unregistered dotted entity aliases instead of silently resolving their final name segment.
- Deleted `datamimic_ce.utils` and its obsolete contract ownership entry.

## Evidence

- ArchKeel violations: 960 -> 922.
- Baseline entries: 7 path-renamed findings added, 40 legacy findings removed.
- Cycle edges: 181 -> 177.
- Root-layout violations: 1 -> 0; runtime-placement violations: 6 -> 0.
- Implementation tests: 259 focused tests, 37 distribution/reference tests, and 18 final
  converter/constructor tests passed.
- Independent verification: 162 focused tests passed and identified the permissive dotted-alias
  fallback; its removal then passed 42 entity tests.
- Full package Ruff: pass.
- Full mypy reached 453 files and failed only on the two existing missing optional `ray` imports.
- Pinned ArchKeel 0.6.0 baseline validation: pass with no new baseline findings; target rules remain
  `FAIL` while 922 baseline violations remain.
- Descriptor oracle: 930 compared, 0 differences, 0 optional-shape variances. Statuses and all
  four canonical projection hashes match Step 0. Snapshot SHA-256:
  `06f879cf2894381d4f8cef627994ce7602697109a7043d1ff2e0651ea2e22a92`.

The existing dynamic converter boundary still carries `Any`; this step did not hide it with a cast
or ignore. Service-backed tests remain unverified because the configured Podman machine is
unavailable. Step 7C is accepted as descriptor- and projection-equivalent to the frozen Step-0
oracle, with the explicit invalid-alias narrowing above.
