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

- **Info, pre-existing.** `selector=""` passes the rule. The run then fails with a raw `KeyError`, and nothing is deleted. The coordinator will file a follow-up issue.
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
