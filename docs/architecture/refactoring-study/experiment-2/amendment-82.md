# Amendment 82: native Runtime capture

2026-10-01. Decision: Astra. Permit only the three nested annotations of
`run(...).captured` in the root contract. Captured DSL data stays live and
native; typed execution controls remain declared. This does not allow unchecked
controls or guarantee transport serialization.

For CE 5.0, importing Runtime `CapturedProducts` and accessing `.root` break.
Repository consumers are migrated; external consumers are UNKNOWN. No shim.
