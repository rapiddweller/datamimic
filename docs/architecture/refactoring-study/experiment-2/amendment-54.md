# Amendment 54: publish lazy output operations from IO

Date: 2026-09-28.

The frozen IO contract names exporter implementations but has no task-facing
operations for final test capture or memstore writes. Publish two existing
write behaviors from IO. Runtime still chooses the zero-row case, merges
workers, walks nested statements, and decides when capture occurs.

This adds two IO interface entries without changing dependency direction or
descriptor behavior. Concrete exporter classes remain inside IO; a proposed
type-only import from exporter core into its memory and diagnostics children
was rejected because it created a component cycle.
