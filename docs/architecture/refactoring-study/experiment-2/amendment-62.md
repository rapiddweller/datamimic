# Amendment 62: native smoke-export payloads

Decision: Astra, 2026-09-29; bounded slice confirmed 2026-10-02 at `25eee585`.

Authoring captures DSL-generated rows; IO writes them and checks the written
count. Rows and target options are open payloads, not fixed routing controls.
The production path constructed two empty RootModels without validation and
immediately unwrapped them. Delete those wrappers; keep SmokeExportRequest.

Use `rows: list[dict[str, object]]` and `params: dict[str, object]`. Preserve
native/nested values, row identity and the registry's shallow options copy.
No JSON narrowing, replacement wrapper or compatibility alias.

IO-API-TYPES permits only qualified name
`datamimic_ce.engine.io.api.smoke_export`, position `request`: four records,
field_path `rows` and `params`, each with annotation `dict[str, object]` and
`object`. Fixed controls and every other method/field remain checked. This is
an explicit narrow permission change, not a claim that the contract is unchanged.

Published ArchKeel 0.8.4 measures 106 violations / 157 counted UNKNOWN positions
at the base, and 110 / 157 after source-only removal. The final amendment result
is 106 / 157 with no invalid-contract diagnostics. Independent probes reject
allowances moved to another method, another field or a misspelled path. Changing
only the fixed `basename` annotation produces two findings at that exact field;
the four allowances stay unchanged. Earlier draft counts (124 / 251) are
historical, not acceptance evidence for this step. No baseline debt is accepted.

No inspected production caller uses ordinary RootModel validation, but unknown
external Python imports could break. Removal follows the approved no-shim target;
it does not claim those classes could never validate another caller's input.
DSL byte-output, failure behavior and before/after replay must remain unchanged.
