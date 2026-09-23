# Amendment 07: activate the typed IO facade

## Decision

Promote the frozen target's `engine.io.contracts` module from planned to public and activate
`boundary_types` for the first real IO facade operation.

## Evidence

- `smoke_export(SmokeExportRequest) -> int` passes `IO-API-TYPES`.
- Authoring no longer imports the mutable exporter registry or runtime contexts.
- Interfaces no longer imports IO; no dependency permission was added.
- The descriptor oracle and all four Authoring projections are unchanged.

## Why ArchKeel calls this a widening

ArchKeel classifies `planned` to `public` as a widening even when the module was already part of
the frozen target. This amendment records target implementation, not a new dependency permission.
