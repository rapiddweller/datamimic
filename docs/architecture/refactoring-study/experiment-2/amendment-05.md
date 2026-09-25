# Amendment 05: activate the DSL and domain APIs

## Decision

Promote the frozen target's `engine.dsl.api` and `domains.api` from planned to public. Activate
`boundary_types` for the first real domain facade function.

## Evidence

- Runtime generator orchestration now imports domain, DSL, and IO symbols only through component
  APIs.
- `domains.api.iter_generator_types() -> Iterator[type]` preserves all 35 registry names and their
  order without exposing the mutable registry dictionary.
- ArchKeel 0.6.0 decides the domain facade signature completely and `DOMAIN-API-TYPES` passes.
- Compact/full capabilities and Authoring reference output are byte-identical to Step 0.

## Why ArchKeel calls this a widening

ArchKeel classifies `planned` to `public` as a widening even when the module was already part of
the frozen target. This amendment records target implementation, not a new dependency permission.
