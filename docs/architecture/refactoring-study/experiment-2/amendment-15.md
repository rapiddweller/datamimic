# Amendment 15: guarantee domain identifiers

Date: 2026-09-24.

## Decision

The 14 domain fields explicitly documented as unique identifiers in service
schemas must be unique per entity type throughout one run, including page
boundaries. Direct batch generation must also satisfy the guarantee. User
approval prioritizes this guarantee over
byte-identical output from the frozen implementation when its random candidates
collide. No XML descriptor is changed.

## Acceptance

- Keep the existing generated ID when its candidate is unused. Handle a
  collision deterministically under a seed; fail explicitly if a finite ID
  space is exhausted. A seeded run must still replay exactly on the new code.
- Compare affected seeded descriptors against the frozen control. Record every
  changed output and show it is caused by collision resolution; do not waive
  unrelated value, count, or schema differences. Other descriptors retain the
  frozen compatibility rule.
- Exercise collisions within a batch, across pages, and across requested worker
  topologies. Prove unchanged output for a collision-free seeded run.
- Keep the unique-field declaration in the entity schema; do not infer the
  contract from prose or field names. Do not treat foreign keys as unique IDs.

This amends only the byte-identical seeded-output clause of protocol item 5
for actual domain-ID collisions. Structural gates, authoring projections, and
the remaining descriptor rules are unchanged. Other possible identity fields,
including doctor NPI and device serial number, need a separate contract review;
this amendment does not silently classify them as unique.
