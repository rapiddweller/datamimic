# Clear and drop runtime review (PR #394, #393 slice 1)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/ce-clear-drop`, base `efb7967a` (#392 merged), head `9ddc1f22` (four commits).
- This review rebinds the [#392 receipt](pr-392-source-file-errors-review.md) and keeps all of its assessments.
- It does not authorize a merge.

## Binding

- **Moved:** the Source, Validation and Unknowns digests.
- **Unknowns:** three new `forward_reference` UNKNOWNs join their group. They are the quoted `ExportOperation` return annotations on the enum's own classmethods.
- **Unchanged:** Contract (`c70eaaf6`), analyzer, and the 20 diagnostics.
- **Measurements:**
  - 1,428 unresolved calls (raised from 1,424; see below);
  - 182 typing positions;
  - 258 unknown positions, the three new forward references;
  - 0 violations.

### Budget raise: `calls_unresolved` 1424 → 1428

**Authorization.** The owner's standing acceptance of 2026-10-22: the raise must be argued, measured, and set to exactly the measured value.

**Verification.** A fresh base collection at `efb7967a` was diffed against the head.

Six unresolved calls are added:
- pymongo `delete_many` and `drop` on the dynamic `database[collection]` receiver;
- SQLAlchemy `engine.begin`, twice, and `…identifier_preparer.format_table` in `_truncate_or_delete_all`;
- `part.strip` in `split_targets`.

Two leave: `consumer.strip`, twice, which moved from `parse_consumer` into `split_targets`.

**History.** At 1114a8ab the methods were named `clear`/`drop`. Two unrelated `dict`/`set` `.clear()` calls then partially resolved to them: `guarded.clear` in the bounded child's `main`, and `_logged_dataset_fallbacks.clear`. That hid two unresolved calls and added false candidate edges.

The methods are now named `clear_table`, `clear_collection`, `drop_collection`, `clear_target` and `drop_target`. Both calls are unresolved again, with no candidates.

## Review

### Parity with EE BC-4.0-016

- **I928:** name, title, template, cause and resolution are identical to EE.
- **Shape rules:** reasons and migrations match `operation_policy.py`. CE also forbids `minCount`/`maxCount` and interval attributes, which is stricter.
- **RDBMS clear:** TRUNCATE on `postgresql`/`mssql`, the same set as EE's `TRUNCATE_ROLLBACK_SAFE_DIALECTS`, with a DELETE fallback.
- **Log lines:** match EE, including `deleted_count=unavailable`.
- **Mongo:** `delete_many({})` and `drop()`.
- **Read-only:** refused with I907.
- **Missing RDBMS table:** a typed I901.
- **External tests** against PostgreSQL 16 and Mongo 8: 13 passed.

### Safety

- **Execution.** The statement runs once in the main process, before any count, source or worker exists. A nested context, an unknown client, a missing `targetEntity`, a mixed target list or any data attribute is refused with I928 before database access.
- **Authoring paths** were probed with a SQLite `db.clear` over 2 rows:

| Command | Without a count | With a count |
|---|---|---|
| `authoring lint`, `dry-run`, `build`, `run`, `run --allow-side-effects` | DM202, rows untouched | — |
| `authoring dry-run` | — | target stripped, reports ok, rows untouched |
| `authoring build` | — | client binding rejected |
| `authoring run --allow-side-effects` | — | I928 in the child, rows untouched |
| `datamimic run` | clears, 0 rows | I928 |

**Conclusion.** Slice 1 cannot clear data through Authoring.

### Design

- `ExportOperation` gains `from_target`, `for_rdbms`, `for_mongodb` and `is_statement_operation`, so no new DSL names are needed.
- `GenerateStatement.client_operations` and `GenerateWorker.run_statement_operation` are added.
- The count gate is exempt only for clear and drop.
- The single-process policy now reads parsed `DELETE` operations instead of matching a `.delete` substring.

**Tests.** The log tests attach their handler to the `DATAMIMIC` logger, so they pass after `setup_logger`. The reproducing order now gives 18 passed.

### Deferred to slice 2 (`feat/ce-clear-drop-authoring`)

- The authoring capability (`catalog.py:146`) and DM401 still list every operation for both client families. Lint therefore accepts `db.drop`, which the runtime refuses.
- DM202 refuses every clear.
- `dry-run` does not apply the I928 shape: a counted clear is reported ok.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review and the EE comparison.
- The SQLite authoring and run probes.
- External, integration and unit clear/drop tests: 73 passed.
- The order-dependence repro: 18 passed.
- The base-vs-head unresolved-call diff and the UNKNOWN diff.
- ruff.
- Native collection and the strict completion gate.

**NOT VERIFIED:**
- Full suites and mypy at this head. The coordinator reports 3,262 unit and 15 integration tests passing.
- CI.
