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

## Addendum: `8feb975a` and `7d92af2d` (Codex bypasses)

**Accepted at `7d92af2d`.** Codex found two bypasses; both are fixed.

**Bypass 1: the call-syntax spelling `db.clear()` with a count.**
- `from_target` does not recognise the parenthesised form. The registry normalises it to CLEAR, so it ran once per page through row dispatch.
- Fix: `consume_exporters` now refuses CLEAR and DROP with I928 unless `statement_operation=True`.
- Only `GenerateWorker.run_statement_operation` passes `True`. `export_product_by_page` forwards it only to the statement's own `dispatch_page`, and nested children dispatch with `False`.

**Bypass 2: an `<include>` inside a `<generate>`.**
- The included step runs in a copied `SetupContext`, so the root-level check accepted a clear there, and it ran once per row.
- Fix: `IncludeTask._execute_with_geniter_context` sets `within_generate`, and the shape check refuses it.

**Blocked at `8feb975a`.** `SetupContext.__deepcopy__` did not copy `_within_generate`. An include inside that include started with `False` again. Probe: include → include → clear under a `<generate count="2">` cleared twice.

**Fixed in `7d92af2d`.** The flag is now copied. Worker projection (`worker_projection` is a deepcopy, sent with dill, which keeps `__dict__`) and nested include copies (`_copy_include_context` is a deepcopy) both keep it. Only the root context is built without a copy.

**Re-probed with SQLite and `datamimic run`.** In every case below the rows stay untouched and no clear runs:

| Case | Result |
|---|---|
| `db.clear(x=1)`, ` db.clear() `, `ConsoleExporter, db.clear()` | I928 |
| `db.clear()` with `numProcess=2` | I928 |
| A nested child with `db.clear()` | I928 |
| `db.drop()` on an RDBMS | I928 |
| Include → clear under a `<generate>` | I928 |
| Include → include → clear under a `<generate>` | I928 |
| Three levels of include under a `<generate>` | I928 |
| The include → include case with `numProcess=2` | I928 |
| A step's `<generate>` that includes a clear | I928 |
| A multiprocess `<generate>` in a step inside a `<generate>` include | I928 |

The intended root and setup-include clears still run once.

**Low.** In a mixed list such as `db.insert, db.clear()`, the insert in the same page runs before the refusal. Nothing is cleared.

**UNKNOWN churn (record by record).**
- The three new `within_generate` positions (value, return `bool`, return `None`) join `inherited_surface`.
- 27 later `SetupContext` positions are re-issued under new ids. Only their `occurrence` index differs; qualified name, position and annotation are identical. They stay in the same group.
- The boundary summary records only update their position counts.

**Binding.**
- Moved: Source, Validation and Unknowns. The receipt now holds 319 UNKNOWN records, and unknown positions rose to 261.
- Unchanged: Contract, analyzer, the 20 diagnostics, and the 1428 / 182 measurements.

**LOCAL VERIFIED:**
- The 12-case run probe at 8feb975a, and the 8-case nested and multiprocess probe at 7d92af2d.
- A content-matched UNKNOWN diff against a fresh collection at `1ca4b09d`.
- Native collection and the strict completion gate.
