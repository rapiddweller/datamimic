# Amendment 157 — runtime package initializer ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

Assign the inert `datamimic_ce.engine.runtime` initializer to `RUNTIME-API`
with an exact module selector. Keep its package selector limited to
`datamimic_ce.engine.runtime.api`.

This declares the physical package marker's owner without broadening imports,
public exports, or dependency permissions.
