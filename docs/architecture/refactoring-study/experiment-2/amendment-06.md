# Amendment 06: activate typed DSL and runtime facades

## Decision

Promote the frozen target's `engine.dsl.contracts` and `engine.runtime.api` from planned to public.
Activate `boundary_types` for both real facade functions.

## Evidence

- Authoring obtains all 35 generator capabilities from declared owner APIs without package scans.
- DSL, domain, and runtime facade signatures are completely decided and pass `boundary_types`.
- Compact/full capabilities and Authoring reference output are byte-identical to Step 0.

## Why ArchKeel calls this a widening

ArchKeel classifies `planned` to `public` as a widening even when the module was already part of
the frozen target. This amendment records target implementation, not a new dependency permission.
