# Amendment 165 — truthful transaction-profile metadata

Date: 2026-10-08. Decision: Astra under Alex's delegation.
Bounded local verification: [Step 132](step-132-transaction-profile-catalog.md).

Person and Patient already preserve `str | Mapping[str, float] | None`.
Their service catalogs incorrectly advertise `(str, dict)`. Change only those
two tuples to `(str, collections.abc.Mapping)`, with the required imports.
Keep field order, descriptions, optionality, getters and runtime behavior.

The existing FieldSpec derives the outer-type name `str | Mapping | None`.
It does not encode or validate generic key/value parameters. Correct the two
matching rows in `docs/data-domains/domain_models.md` to the existing precise
getter annotation. Add no schema machinery, mapping conversion or doc generator.

Under protocol item 6, intentionally permit the two catalog tuples, their
derived type strings and one transaction-profile line each in the Person and
Patient named reference pages. Keep the renderer and transports unchanged.
Dicts remain accepted Mapping values. External consumers depending on dict
type identity or exact old reference bytes remain UNKNOWN.

Acceptance requires a real non-dict Mapping returned by both services to match
the catalog, with identity, backing mutation and native JSON behavior preserved.
Compare all 23 named pages and schemas; isolate exactly these two field changes.
The four frozen projections omit named detail pages and must remain unchanged
separately. Preserve descriptors, frozen records, comparators, baselines,
architecture permissions and EE source. Full acceptance remains open.
