# Step 203 — selector-backed variable query rows

IO query results now declare `list[dict[str, object]]`. Query-selected columns and
native cell values remain data; Runtime still owns selector evaluation and timing.
[Amendment 203](amendment-203-variable-query-rows.md) explicitly authorizes only this
return's row map and cell depth. This extends the target with accepted opacity;
it does not prove closed native types or universal custom-client contracts.

Production change: one return annotation. The executable function/file AST,
Runtime callers and facade publication are unchanged. No coercion, validation,
copy, driver change, new dependency or baseline change.

Local characterizations preserve full-pool/direct-page list identity, count/read
ordering, noncyclic row aliases, cyclic deep copies, zero/empty windows, native
Decimal/date/bytes/nested values and original exceptions. Injected scalar-list
clients still pass through unchanged. Native SQLite exercises actual query-to-map
conversion; Mongo find/aggregate tests use a driver seam, not a live server.

Independent published ArchKeel 1.1.1 matcher proof covers 20 CLI fixtures.
Both exact selectors accept; each selector alone retains the other finding.
Wrong names/positions/paths/depths and broader annotations retain FAIL findings.

Fresh before/after canonical reports: **13 -> 12 violations**; only
`read_variable_query` is removed. All other 12 canonical findings and all 254
canonical UNKNOWN records are exactly preserved (200 scalar UNKNOWN positions).
Dependency, module/package, import, cycle, coverage and ownership observations
are equal. Both reports parse 488/488 files with 100% AST coverage.
`declared_rules: FAIL` remains. No hidden components or DSL-ledger promotion.

Source commit: `5c5989d37fcc02cb51e64a181638e38a9a77bdea`; its complete tracked
tree equals reviewed `72ed6c33`. Independent final review: GO.

LOCAL VERIFIED: 2399 unit passes, 11 skips, one expected failure; final focused
checks 185 PASS, including the last test-fixture correction. Package Ruff, full
MyPy (488 files) and 13 architecture definition checks pass. Runtime source
was unchanged during these checks. [Receipt](step-203-variable-query-rows-receipt.json).
CI-ONLY VERIFICATION: pending for the integrated source/evidence head.

External static consumers/custom-client row shapes, general
native value closure, full DSL/EE behavior and the remaining target remain open.
