# Step 06: consolidate domains, resources, and interfaces

## Change

- Moved converters under `domains/converters` and shipped demos under `resources/demos`.
- Moved CLI and MCP adapters under `interfaces`; updated console entry points and resource lookup.
- Removed all four legacy root paths without compatibility wrappers or behavior changes.
- Made the descriptor inventory use tracked XML files so ignored run output cannot contaminate the oracle.

## Evidence

- ArchKeel violations: 1,072 -> 1,033.
- Cycle edges: 184 -> 181.
- Domain, resource, and interface placement violations: 32 -> 0.
- Root-layout violations: 8 -> 1; only the deliberately deferred mixed-owner `utils` package remains.
- Baseline entries: 66 path-renamed findings added, 105 legacy findings removed.
- Implementation tests: 97 passed.
- Independent tests: 72 focused tests and the MCP stdio integration passed.
- MCP SSE remained unverified in the verification sandbox because it forbids binding a local socket.
- Wheel build: pass; both console scripts target `interfaces`, all 169 demo resources are present,
  and no legacy CLI, MCP, converter, or demo path is packaged.
- Full package Ruff: pass.
- Full mypy reached 461 files and failed only on the two existing missing optional `ray` imports.
- Pinned ArchKeel 0.6.0 baseline validation: pass; the target rules remain `FAIL` as expected while
  1,033 baseline violations remain.
- Descriptor oracle: 930 compared, 0 differences, 1 tolerated evidenced optional-shape variance.
  Statuses and all four canonical projection hashes match Step 0. Snapshot SHA-256:
  `7567771c280351698355af634d6882432bd335c1a5c73fdbd94feeb7df4ad74e`.

Service-backed tests remain unverified because the configured Podman machine is unavailable.
Step 6 is accepted as behavior-equivalent to the frozen Step-0 oracle.
