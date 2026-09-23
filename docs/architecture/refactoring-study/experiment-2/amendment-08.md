# Amendment 08: activate the typed Authoring facade

## Decision

Promote the frozen target's `authoring.api` module from planned to public and activate
`boundary_types` for its application operations.

## Evidence

- All five Authoring operations use Authoring-owned request and result models.
- Interfaces no longer import Authoring service, diagnostic, rule-catalog, or spec internals.
- The live MCP schema hash and all four Authoring projection hashes are unchanged.
- No component dependency permission was added.

## Why ArchKeel calls this a widening

ArchKeel classifies `planned` to `public` as a widening even when the module was already part of
the frozen target. This amendment records target implementation, not a new dependency permission.
