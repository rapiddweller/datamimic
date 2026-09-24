# Amendment 16: target-state boundary for unique IDs

Date: 2026-09-24.

## Decision

Amendment 15 guarantees the 14 declared domain IDs are unique within one
generated run. It does not promise that an ID is absent from a target database.
The target's primary-key or unique constraint is the final check against rows
already stored there. On an insert conflict, report the write failure; do not
silently skip, query-and-rekey, or change the generated ID. The caller must
explicitly choose a reset/isolated target or an existing upsert operation.
Upsert matches the target's primary key, not every unique index.

`unique="true"` on a DSL key, variable, or generate retains its existing
selection/generator meaning. It is not a target lookup and is not required to
activate the domain-ID guarantee. No new DSL attribute or target-policy knob
is introduced by this amendment.

## Acceptance

- Same descriptor, seed, sources, engine version, and initial target snapshot:
  compare generated values and the final target rows. A seed alone does not
  freeze sources, constraints, defaults, triggers, or concurrent writers.
- Existing conflicting target row plus explicit insert: fail without changing
  the ID. Existing row plus explicit upsert: exercise the primary-key behavior.
- Do not claim an all-or-nothing run transaction: CE exports pages separately,
  so a later failed page may leave earlier pages committed.
- Use focused runtime/target tests and the descriptor oracle. Do not add a
  separate architecture gate for a behavior that requires execution.

This narrows the interpretation of target reproducibility; it does not relax
any descriptor, projection, architecture, or local test acceptance gate.
