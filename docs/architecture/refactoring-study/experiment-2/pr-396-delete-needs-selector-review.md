# Delete needs a selector review (PR #396, #393 slice 3)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/ce-delete-needs-selector`, base `c648a0a9` (#395 merged), head `6e0bea4f` (three commits).
- This review rebinds the receipt on development and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source, Validation and Unknowns digests. Against a fresh base collection at `c648a0a9`, the Unknowns move is only re-issued `fact_ids`/`evidence_ids` plus one summary count; the 319 ids and their groups are unchanged.
- **Unchanged:** Contract (`c70eaaf6`), analyzer and the 20 diagnostics.
- **Measurements:** 1,428 unresolved calls, 182 typing positions, 261 unknown positions, 0 violations.
- The rebind uses a gate run that finished without a collector error.

## Rule

A `delete` that reads a database `source` without a `selector` fails with I928 before any database access. Without a selector, it removes everything the source returns. The owner's decision keeps the rule narrow:

- **Still valid:** file-source deletes, generated-key deletes, and selector deletes, including Mongo `filter: {}`.
- **One rule, two callers:** `GenerateStatement.delete_intent_problem` is used by:
  - the runtime (`GenerateTask._assert_delete_selects_rows`), before the count;
  - bounded execution (`neutralize_for_dry_run`), before it strips targets.

## Probes

All probes use SQLite, with 2 rows in the table before each command.

| Case | `datamimic run` | dry-run | Build |
|---|---|---|---|
| Whole source (`type` or `sourceEntity`), no selector | I928, 2 left | I928 | I928 |
| Nested in a `<generate>` | I928 | I928 | I928 |
| Counted, in the entry | I928 | I928 | I928 |
| In a step, using the entry's client | I928 | I928 | I928 |
| Counted, in a step, using the entry's client | I928 | I928 | I928 |
| In a step, using the step's own client | I928 | I928 | refused (step clients) |
| Selector `WHERE id = 1` | 1 left | ok, 2 left | rejected (cardinality unknown) |
| Selector `SELECT *` (explicit) | 0 left | ok | rejected (cardinality unknown) |
| File source | 1 left | ok | ready |
| Generated keys | 1 left | ok | ready |

Bounded execution touched no row in any case.

## History

- **468345bc (blocked).** `database_ids` covered only the current root. A counted whole-source delete in an included step reached Build `ready`, while `datamimic run` refused it.
- **e235d222 (blocked).** The fix read the entry's ids with a second XML parse. That added one unresolved lxml call, so `calls_unresolved` rose from 1,428 to 1,429, over budget. Passing those ids explicitly also replaced the step's own ids, so dry-run regressed for a step that declares its own client.
- **6e0bea4f (accepted).** One shared set is passed as `set()`. Each transformer call adds its root's client ids. The entry is transformed before any step, so its clients stay visible to every step, and a step's own clients are added. There is no second parse and no new unresolved call.

## Findings (not P1)

- **Superseded by the `ee592e12` addendum below.** At 6e0bea4f, `selector=""` passed the rule. Without a `count` the run failed with a raw `KeyError`, but with a `count` it deleted every row. For a delete, a blank selector now gives I928. #397 tracks the raw `KeyError` for other operations.
- **Info.** The shared set also makes one step's clients visible to later steps. Such a reference fails at runtime anyway, so at worst dry-run reports I928 where the run reports a missing client.
- **Tests.** The mock change in `test_generate_task.py` (`delete_intent_problem.return_value = None`) is needed for a `MagicMock` statement. The DSL tests and the probes cover the real behavior.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- 11 scenarios × run, dry-run and Build, at each of the three heads.
- The unresolved-call lookup.
- ruff.
- A clean gate run.
- The strict completion gate after the rebind.

**NOT VERIFIED:**
- Full suites, mypy, and the external services. The coordinator reports these.
- CI.

## Addendum: `ee592e12` (Codex P1, blank selector)

**Accepted.** The hole was real.

- **The hole:** with `count="5" source="db" sourceEntity="items" selector="" targetEntity="items" target="db.delete"`, the code at `c32e8343` deleted both rows. The run exited 0 and logged "Cannot get length…". The source reader treats a blank selector as absent and reads the whole entity.
- **The fix:** `delete_intent_problem` treats an empty or whitespace selector as no selector.

Re-probed with SQLite, 2 rows in the table:

| Case | `datamimic run` | dry-run | Build | Rows left |
|---|---|---|---|---|
| `selector=""` with a count | I928 | I928 | I928 | 2 |
| `selector="   "` with a count | I928 | I928 | I928 | 2 |
| `selector="&#10;"` with a count | I928 | I928 | I928 | 2 |
| Blank selector in an included step | I928 | I928 | I928 | 2 |
| A real selector (`WHERE id = 1`) | deletes 1 row | ok | rejected (cardinality unknown) | 1 (run) |

#397 stays open for the raw `KeyError` that other operations hit with a blank selector.

**Binding.**
- Source, Validation and Unknowns move. Against a fresh collection at `6e0bea4f`, the Unknowns move is only re-issued `fact_ids` and `evidence_ids`. The 319 ids and their groups are unchanged.
- Contract, analyzer and the 20 diagnostics are unchanged, and so are the 1,428 / 182 / 261 measurements.

**LOCAL VERIFIED:**
- The hole reproduced on the old code.
- The 5-case probe at `ee592e12`.
- `test_clear_drop_clients` and the delete DSL tests: 39 passed.
- ruff.
- A clean gate run.
- The strict completion gate after the rebind.
