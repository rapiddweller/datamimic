# Amendment 09: activate the typed Resources facade

## Decision

Promote the frozen target's `resources.api` module from planned to public and activate
`boundary_types` for its two packaged-demo operations.

## Evidence

- Interfaces no longer discover `datamimic_ce.resources` by a package-name string.
- `demo_root() -> Traversable` and `demo_names() -> Iterator[str]` pass `boundary_types`.
- The existing filesystem-only copy behavior is unchanged; no new packaging behavior was added.
- No component dependency permission was added.

## Why ArchKeel calls this a widening

ArchKeel classifies `planned` to `public` and adding `boundary_types` as widenings even though both
implement the frozen target. The amendment records facade activation, not a broader dependency.
