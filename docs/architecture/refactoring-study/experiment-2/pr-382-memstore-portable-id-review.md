# Portable memstore id review (PR #382)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `docs/memstore-portable-id`, base `c7624b34` (#381 merged), head `afc1ec06` (one commit).
- This review rebinds the [#381 receipt](pr-381-dotable-mapping-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source digest only, through the `MemstoreModel.id` description string.
- **Unchanged:** Validation, Contract (`c70eaaf6`), analyzer, Unknowns, the 313 UNKNOWN records and the 20 diagnostics.
- **Measurements:** 1,424 unresolved calls, 182 typing positions, 255 unknown positions, 0 violations.

## Review

**The change is text only.**
- The `MemstoreModel.id` description and `docs/examples/authoring.md` (example id `store` → `mem`).
- The plugin's `project-structure.md` rule 2.
- No engine behaviour changes.

**The EE claim holds**, checked in datamimic-ee at `5d19c968`.
- `BREAKING_CHANGES.md`, BC-4.0-038 (withdrawn from the ledger): a setup `<memstore id="…"/>` is accepted with warning `W005` and ignored. It creates no custom client, source or target id, and the built-in `target="mem"` / `source="mem"` behaviour is unchanged.
- In code, `W005` is `IssueCode.LEGACY_MEMSTORE_DECLARATION` (`errors/catalog/codes.py:450`). EE's own use case (`engine/dsl/contract/element_usage.py:884`) declares `<memstore id="mem"/>`.
- The readback's `type=` works in EE as the entity fallback: `helpers/source_entity.py`, `stmt.source_entity or stmt.type or stmt.name`.
- **Probe:** an EE `authoring dry-run` of the doc example emits the `W005` warning on stderr ("deprecated and ignored; execution continues").
- **Corollary:** a named store such as `id="store"` has no EE counterpart, so "Other ids are a CE-only extension" is true.

**CE.**
- The doc example and its acceptance, extracted verbatim, Build `ready` with no diagnostics.

**Redaction and over-engineering.** Not applicable: the change is static text.

**Note.** The EE bounded dry-run additionally demands a literal count or `maxCount` on the source-driven readback. That is EE authoring policy, not the memstore form, and it is outside this doc's CE Build example.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- The EE ledger and code references above.
- The EE `W005` emission.
- The CE Build of the extracted example.
- `agent-plugin-check`.
- 185 doc, example, plugin and capability unit tests.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- A complete EE execution: it needs runtime settings (MinIO and others) this machine lacks.
- ruff and mypy at this head. The coordinator reports both clean.
- CI.
