# Amendment 183 — native XML rows at ExportSession

2026-10-10. Decision: Astra, delegated architect. Base `ce3deb609318a55302ab4e3855f113e39984b8ee`.

IO owns conversion and export dispatch; Runtime owns order and lifecycle.
Raw XML rows require string-keyed dictionaries with native values. Converted
rows remain `list[object]`: `#text` may return any native value, including a
scalar. JSON-only values or dictionary-only converted rows would be incorrect.

Annotate only the existing XML slots in `PreparedPage`, `prepare_page`,
`consume_exporters` and both Runtime export-order functions as
`list[dict[str, object]]`, inside the existing product map where applicable.
Function bodies, tuple alternatives and `ExportMetadata` remain unchanged.

Supersede Amendment 181's raw XML hold only for `IO-API-TYPES` at
`datamimic_ce.engine.io.api.ExportSession.prepare_page`, position `xml_rows`,
empty `field_path`, full annotation `list[dict[str, object]]`. Add exactly
two selectors: the single map occurrence without `container_depth`, and its
native value at depth 2. Preserve the existing 22 selectors. This is accepted
opacity, not full type closure. No alias, metadata or blanket object grant.

XML dispatch keeps the original list and rows; conversion retains native
`#text`, Decimal and nested values. Nonempty metadata keeps identity and the
three-item tuple; empty metadata keeps the two-item tuple. Conversion precedes
registration lookup and child writes. Native TypeError/AttributeError and
dictionary-subclass failures retain their timing and identity.

Static compatibility narrows: external `list[dict[str, int]]` is invariant and
does not satisfy this contract; integer keys and read-only mappings also do
not. Typed callers must declare the existing mutable native-row contract,
without casts or copies. Dynamic runtime inputs keep their existing behavior.
External typed callers are UNKNOWN, and bare internal producers remain an
incomplete static proof.

PreparedPage alias findings, nested-source returns, Properties and Cache remain
open. SQL Amendment 155, EE, ownership, public/dependency grants, baseline,
budgets and oracle are unchanged. Fresh ArchKeel 1.1.0 report: FAIL26 (27 → 26),
with all 254 canonical / 200 measured UNKNOWNs preserved. The two alias-internal
bare-map findings become precise map findings; 24 other findings stay identical.
Two new allowance facts include one accepted native-value opacity.
No whole-target or full DSL/EE acceptance is claimed.

LOCAL VERIFIED: existing 14 dispatch tests and expanded 17 native/error tests
pass before source edits; annotation and exact contract guards fail, then all
32 focused tests pass with identical test bytes. After one assertion line wrap
(identical AST), 157 export/capture/XML/boundary tests pass with one expected
failure. The Makefile's 13 definition checks pass in the project venv; its uvx
launcher cannot access the sandboxed cache. Package/changed-test Ruff and full
MyPy (488 files) pass. Explicit-source type probes accept native object rows
and reject integer keys, read-only maps, narrow integer-valued lists and invalid
metadata. Function bodies and the prior 22 selectors are unchanged.

Independent QA: 45 tests, native identity/error probes, four static negative
cases and 20 selector/alias counterexamples pass. Native amendment validation
retains the IO widening but exits 2 with the same 19 usage-UNKNOWN diagnostics
and 16 baseline-new groups; no machine amendment is emitted.
CI-ONLY VERIFICATION: new-head checks pending.
