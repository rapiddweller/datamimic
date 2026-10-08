# Amendment 158 — IO package initializer ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

Assign the inert `datamimic_ce.engine.io` initializer to `IO-API` with an exact
module selector. Keep its package selector limited to
`datamimic_ce.engine.io.api`.

This declares the package marker's owner without broadening imports, public
exports, or dependency permissions.
