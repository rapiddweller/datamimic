# Actionable remediations review (PR #372)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/actionable-remediations`, base `3eacef1c` (#371 merged), head `0abeb9c7`.
- This review rebinds the [slice (c) receipt](issue-356-project-acceptance-c-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Source:** the only binding that changes. The new digest is in `completion-unknowns.json`.
- **Unchanged:** validation, contract, analyzer, the 20 diagnostics and the 313 UNKNOWN records.
- **Measurements:** 1,424 unresolved calls, 178 typing positions, 255 unknown positions. The call counts are identical to the base, because the new arguments are literals.

## Source review

**Correctness.** `catalog_diagnostic(..., remediation=None)` falls back to the rule's own remediation. Both `_reject` helpers pass it through.

Four rejections now name their fix:

| Rejection | New remediation |
|---|---|
| Memstore handoff without roles | The identifier/foreign_key role pair |
| Memstore target nobody reads | Read it back, or use a file target |
| Unknown expectation field | Declare it as a `<key>` |
| Unknown cardinality | The capture reason lists the count fixes |

The four new tests fail without the change.

**Redaction.** Every text is static, with placeholders such as `<producer>` and `<memstore id>`. No descriptor value is echoed.

**Over-engineering.** None. It is one optional parameter and literal texts.

### Findings (not P1; follow-ups)

**Low: the unknown-cardinality reason** (`dryrun.py:675-678`).
- The reason is shared by every generate whose cardinality is not static. That includes database, Mongo and memstore sources, and generates with no count at all.
- For a source-backed generate, "a count expression over the rows it produces" is not provable: dryrun replaces such a count with `max_count`, and the capture stays capped.
- The advice is right for the scripted generate in the new test.
- It also repeats remediation in a cause field that acceptance already pairs with its own capped/unknown remediation.
- Condition the text on `stmt.source is None`, or keep the reason causal and let the remediation carry the fix.

**Low: the plugin's `project-structure.md`** lists `sql/*.scr.sql` for "schema, cleanup and delivery SQL" as part of a project that Build proves. Build refuses SQL `<execute>` anywhere in the graph, as `ce.md` states. A note that SQL steps take a project outside bounded proof would avoid a dead end.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- Tests: 174 passed across the new remediation tests, project build, acceptance, dryrun bounds, capture boundary and docs.
- `agent-plugin-check`.
- ruff and mypy.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites.
- CI.

## Addendum: `a53f3da8`, both Lows resolved

- **Unknown-cardinality reason:** the count hint is now appended only when `stmt.source is None`. A source-driven generate keeps the plain causal reason, and its fix stays in the capture remediation.
- **Plugin reference:** `project-structure.md` now marks `sql/` as "real runs only; Build refuses SQL execute".
- **Binding:** the source digest is rebound. Validation, contract, the 20 diagnostics and the 313 UNKNOWN records are unchanged, and the measurements stay at 1,424/178/255.
- **Gates:** 87 related tests passed; `agent-plugin-check`, ruff and mypy are clean; the strict completion gate passes.
