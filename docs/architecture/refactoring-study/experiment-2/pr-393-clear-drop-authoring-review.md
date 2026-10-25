# Clear and drop authoring review (#393 slice 2)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/ce-clear-drop-authoring`, base `96aa455e` (#394 merged), head `52c00e12` (one commit).
- This review rebinds the [#394 receipt](pr-394-clear-drop-runtime-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source, Validation and Unknowns digests.
- **Unknowns:** the same 319 ids in the same groups. Against a fresh base collection, only `fact_ids`/`evidence_ids` and one summary count changed.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, and the 20 diagnostics.
- **Measurements:** 1,428 unresolved calls, 182 typing positions, 261 unknown positions, 0 violations.

## Safety

Probes ran against real external clients: Postgres 16 `ce393-pg` (table `dm_probe_items`, 2 rows) and Mongo 8 `ce393-mongo` (collection `dm_probe_docs`, 2 documents), with `RUNTIME_ENVIRONMENT=development`. The table counts rows left after each command.

| Command | Postgres clear | Mongo clear | Mongo `drop()` |
|---|---|---|---|
| `authoring lint` | ok, 2 left | ok, 2 left | ok, 2 left |
| `authoring dry-run` | ok, `not_executed` warning, 2 left | ok, warning, 2 left | ok, warning, 2 left |
| `authoring build` | ready with the warning, 2 left | ready with the warning, 2 left | ready with the warning, 2 left |
| `authoring run` | warning, 2 left | warning, 2 left | warning, 2 left |
| `authoring run --allow-side-effects` | cleared, 0 left | cleared, 0 left | dropped |
| `datamimic run` | cleared, 0 left | cleared, 0 left | dropped |

Bounded execution never ran a clear or drop without the opt-in.

Invalid shapes against Postgres; no rows were touched in any case:

| Case | Lint | Dry-run and Build | `datamimic run` |
|---|---|---|---|
| Counted clear | passes | I928 with `ce_error` | I928 |
| Clear nested in a `<generate>` | passes | I928 with `ce_error` | I928 |
| Clear without `targetEntity` | passes | I928 with `ce_error` | I928 |
| Unknown client | DM401 | DM401 | I928 |
| `db.drop` on an RDBMS client | DM401, now per client family | DM401 | I928 |
| Clear in a step included from a `<generate>` | passes | refused (bounded includes must be literal and at setup level) | I928 |
| Clear in a setup-level step | passes | skipped with the warning | clears |

Setup-level `<if>` and `<while>` are not valid CE children (I604), so they need no skip path.

## Review

**Shared shape check.** `GenerateStatement.operation_intent_problem` now serves both the runtime and bounded authoring. The client check stays runtime-only; lint's DM401 covers unknown clients. Leaving out a new lint rule id is right: it would need an EE counterpart, and dry-run and Build already report I928 with its catalog identity.

**Skip mechanics.**
- `neutralize_for_dry_run` records dropped statements by `id()` and filters them out of every composite and of the root.
- Includes reuse the same transformer and the same `skipped` list.
- `_WorkerSuccess.skipped_operations` is a tuple of names appended last, matching `_validated_worker_success`'s positional rebuild, and needs no new pickle globals.

**Acceptance and codec.**
- Acceptance projection excludes statement operations by target.
- The DM JSON codec drops `EXIST_COUNT` only for them.
- `script_semantics.names_statement_operation` uses only the public `parse_consumer` and `ExportOperation`.

### Findings (not P1)

- **Low: readback after a skipped clear.** Without side effects, a later source readback of the same table reads the rows the skipped clear would have removed. The `not_executed` warning ("its effect is not proved") covers this, but such evidence describes the state before the clear.
- **Low: proof gap for a step included from a `<generate>`.** Such a clear is skipped rather than refused by the shape check, because the transformer sees the step root as top level. Bounded includes inside a `<generate>` are refused today, so this path cannot be reached.
- **Known limit:** a cleanup-only project has no captured product, so Build rejects it.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- The 18 external-client probes and the 36 shape probes.
- `test_clear_drop_authoring` and the clear/drop integration tests: 29 passed.
- ruff.
- A fresh base collection, the UNKNOWN content diff, and the strict completion gate.

**NOT VERIFIED:**
- Full suites, and mypy at this head. The coordinator reports both clean.
- CI.

## Addendum: `ac0e5ad3` and `139558a5` (skip-only dry-run)

**Accepted at `139558a5`.**

**What changed.** A dry-run that only skipped a clear or drop now reports ok, with the `not_executed` warning.

**Blocked at ac0e5ad3.** That head set `base_run_ok = base_run_ok or bool(skipped)`. Build's gate reads that value, so adding a skipped clear turned a rejected zero-row Build into `ready`.

**Fixed in 139558a5.** A skip now counts only when nothing else was captured: `base_run_ok or (bool(skipped) and not captured.products)`.

**Re-probed against ce393-pg.** The table stays at 2 rows after every command.

| Project | dry-run | Build |
|---|---|---|
| A zero-row product with `exact_count 0` and a skipped clear | rejected | rejected |
| The same project without the clear | rejected | rejected |
| Cleanup-only | ok, with the warning | rejected (no products) |
| Clear followed by rows | ok | `ready`, with the warning |

**Low.** With a skipped clear present, the specific "Bounded execution produced no captured rows." diagnostic is suppressed. A zero-row project with a clear is therefore rejected only by Build's generic gate message. Emitting that diagnostic whenever a product exists without rows would name the reason.

**Binding.** Source and Validation move. Unknowns, Contract and the 20 diagnostics are unchanged, and so are the 1,428 / 182 / 261 measurements.

**LOCAL VERIFIED:**
- The four probes.
- `test_clear_drop_authoring`.
- ruff.
- Native collection and the strict completion gate.

## Addendum: `70d4e22a` (Codex P2 threads)

**Accepted.**

**Thread 1: the coordinator's claim holds, so no code change is needed.**
- `_literal_include_graph` walks every `<include>` of the entry and of each step with `document.iter("include")`.
- It refuses an include unless the include is a direct child of `<setup>` and has a literal, contained uri.
- No alias maps to `include`: the only aliases are `iterate` and `id`.
- Dry-run and `authoring run --allow-side-effects` both call `_validate_bounded_includes` before the transformer. A clear in a step included from a `<generate>` therefore never reaches `neutralize_for_dry_run`.
- Probe against ce393-pg: both commands give a `side_effect` error, and the 2 rows stay in the table.

**Thread 2: `executed_operations`.**
- With side effects allowed, a clear or drop that passes the shape check is recorded at transform time.
- The child returns `_WorkerSuccess` only when the run raised nothing, so a recorded operation means it ran.

Probes against ce393-pg with side effects allowed:

| Case | Result | Rows left |
|---|---|---|
| Cleanup-only `authoring run --allow-side-effects` | ok, no diagnostics | 0 |
| Same, read-only client | I907 failure | 2 |

The field is appended last, matching the positional rebuild. It holds names only, so the pickle payload needs no new globals.

**Low: a zero-row product next to a clear fails without a reason.** With a skipped or executed clear, the "no captured rows" diagnostic is suppressed. Probes:
- `authoring run --allow-side-effects` fails with exit code 1 and an empty diagnostics list.
- dry-run fails with only the `not_executed` warning.

Suggested fix: emit the no-rows diagnostic whenever `captured.products` exist and none has rows, and suppress it only when there are no products.

**Binding.** Source and Validation move. Unknowns, Contract and the 20 diagnostics are unchanged, and so are the 1,428 / 182 / 261 measurements.

**LOCAL VERIFIED:**
- 8 probes.
- `test_clear_drop_authoring`.
- ruff.
- Native collection and the strict completion gate.
