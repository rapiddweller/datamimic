# Amendment 159 — exporter package initializer ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

Assign the inert `datamimic_ce.engine.io.exporters` initializer to
`EXPORTERS-REGISTRY` with an exact module selector. Keep the registry package
selector limited to `datamimic_ce.engine.io.exporters.registry`.

The registry is the existing composition entry for exporters; the marker adds
no exports or behavior. This does not broaden imports or dependency permissions.
