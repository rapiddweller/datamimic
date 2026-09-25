# Amendment 04: reset the logger call-resolution measurement

## Decision

Keep the stdlib named-logger implementation and reset only the `calls_unresolved` ratchet from
1,340 to 1,408. No dependency permission or target rule changes.

## Evidence

- The change removes 56 contract violations and the observed `interfaces -> runtime` edge.
- All changed modules receive the same `logging.getLogger("DATAMIMIC")` object; logger setup still
  applies its handler, level, propagation, and worker formatter.
- ArchKeel changes exactly 68 `logger.*` calls from resolved to unresolved: 28 `error`, 27 `debug`,
  12 `warning`, and 1 `exception`.
- Rewriting one call as `logging.Logger.error(logger, ...)` makes ArchKeel resolve it and reduces
  the scalar by one, proving the delta is receiver classification rather than dynamic dispatch.

## Why this is not accepted architecture debt

The normal stdlib call is clearer and has a concrete `logging.Logger` runtime type. Rewriting 68
calls into class-method form would couple production style to an analyzer workaround. The reset
keeps the measurement active from the new value and records the limitation explicitly.
