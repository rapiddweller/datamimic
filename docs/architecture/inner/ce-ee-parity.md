# CE / EE parity matrix (CE 5.0)

Status: first version. It tracks CE issue #387. Source: CE `10ac45a9` (`development`), EE `fc7c0d59e`
(`development`). Date: 2026-10-25. The EE side is done in a separate EE session against the same
[conformance cases](../../../tests_ce/conformance/README.md).

## How to read it

Every row has one status:

| Status | Meaning |
|---|---|
| `identical` | CE and EE behave the same. The evidence column says how it was checked. |
| `CE-extension` | CE has it, EE does not. It is documented and on purpose. |
| `EE-only` | EE has it, CE does not. It is documented and on purpose. |
| `gap` | CE and EE differ and nobody decided it. Each gap has an owner and a next step. |
| `unverified` | Not compared yet. Each one is listed in [Open rows](#open-rows). |

The release gate: no `gap` and no `unverified` row stays open for CE 5.0.
Each EE-side gap links its issue in the EE tracker.

## Method

The facts come from the code and from runs of the same inputs in both editions. Nothing comes from memory.

1. Issue catalogs: load `ISSUE_DEFINITIONS` and `ERROR_TEMPLATES` in each edition, then compare by code name and value.
2. Authoring: run `authoring schema`, `authoring --help` and `authoring reference --topic rules` in each edition.
3. Logging and exit codes: run one valid and one invalid descriptor with `run` in each edition.
4. Behavior cases: [tests_ce/conformance](../../../tests_ce/conformance/README.md).

## Decision: log layout (2026-10-25, owner)

Both editions use: milliseconds in the timestamp; the worker label `MAIN` without the pid; a
`CONTROL kind=start` record; the error record before `CONTROL kind=end`; no `USER_ERROR` prefix.
CE is done (#399). EE follows in [EE #89](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/89).

## Error handling

| # | Behavior | CE | EE | Status | Owner / next step |
|---|---|---|---|---|---|
| E1 | Issue code names and values | 105 codes | 411 codes. 104 of the CE codes have the same name and value. | `gap` | `TASK_TOTAL_ROW_BUDGET_EXCEEDED` (`I955`) exists only in CE. Reserve it in EE first (CE rule: CE codes are a subset of EE). Owner: EE session, then CE. Issue #400. |
| E2 | Code name, title and severity of the 104 shared codes | same | same | `identical` | Catalog comparison. |
| E3 | Error code templates (`E0xx`, 15) | same | same | `identical` | Catalog comparison. |
| E4 | EE-only issue codes | none | 307 | `EE-only` | EE features (native engine, ML, HL7, platform). No CE action. |
| E5 | Message `DATETIME_MAX_BEFORE_MIN` (`I430`) | "must be greater than or equal to" | "must be greater than" | `gap` | Both editions raise only when `max < min`, so equal values pass. The CE text is right. Owner: EE, [EE #84](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/84). |
| E6 | Message `SOURCE_FILE_NOT_FOUND` | "Source file '{name}' not found" | adds "in task workspace" | `CE-extension` | CE reads from the descriptor directory and has no task workspace. Keep both texts. |
| E7 | Message `TASK_KEY_SCRIPT_INVALID_TYPE` | names the type only | also prints the value | `CE-extension` | CE redacts descriptor values in diagnostics (secrets in parameter environments). Keep. |
| E8 | Resolution `TASK_MP_PLATFORM_UNSUPPORTED` | "multiprocessing or ray" | "fork, spawn, or forkserver" | `gap` | The two editions name different values for the same attribute. Owner: CE and EE session decide the valid values, then align the text. Issue #400. |
| E9 | Exit codes of the CLI | 0 ok, 1 error, 2 usage | 1 error (run), 2 usage | `identical` | Observed with one valid and one invalid descriptor. |
| E10 | Order of records on a user error | error record, then `CONTROL kind=end` | `ERROR USER_ERROR \| <message>`, then `CONTROL kind=end` | `gap` | CE changed to the agreed order and has no prefix. EE must drop the `USER_ERROR` prefix and keep the order: [EE #89](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/89). Decision on #399. |
| E11 | Multi-line error text in one log record | one physical line (`\n` escaped) | several physical lines | `gap` | CE did this in #384. Owner: EE, [EE #85](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/85). |
| E12 | `run` CLI | `datamimic run DESCRIPTOR` | `datamimic-ee run DESCRIPTOR TASK_ID RUNTIME_CONFIG_JSON`, needs Redis and MinIO settings | `EE-only` | Platform coupling. The conformance runner uses the in-process API, not the CLI. |

## Logging

| # | Behavior | CE | EE | Status | Owner / next step |
|---|---|---|---|---|---|
| L1 | Record layout | `time \| LEVEL \| DATAMIMIC \| worker \| message` | same layout | `identical` | Run output. |
| L2 | Timestamp | milliseconds (`20:16:20,418`) | milliseconds | `identical` | CE fixed in #399. The old `datefmt` slice cut the fraction. Test: `test_log_lines_carry_milliseconds_and_the_plain_main_label`. |
| L3 | Worker label | `MAIN` | `MAIN-<pid>` | `gap` | Agreed label: `MAIN`; the pid is in `CONTROL kind=start`. EE changes: [EE #89](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/89). |
| L4 | Level names | `WARN ` for warnings | `WARN ` | `identical` | Both register the same level name. |
| L5 | `CONTROL kind=start` record (`descriptor`, `pid`) | present since #399 | present | `identical` | Test: `test_run_logs_one_start_event_with_descriptor_name_before_the_end_event`. |
| L5b | Banner lines (`Start data generation`, `Log level`, `Runtime config`, `FASTOPS`, `Evaluation engine`) | none | present | `EE-only` | EE runtime detail. No CE action. |
| L6 | `CONTROL` kinds `end` and `policy` | both | both | `identical` | Run output and source. |
| L7 | `CONTROL` kinds `execution_plan`, paging policy and `RATE_CARD` | none | present | `EE-only` | Tied to the EE data source engine. No CE action. |
| L8 | `OPERATION` records of clear and drop | specified and tested | specified in the EE guide | `identical` (specification) | [Guide](../../guides/destructive-database-operations.md). EE test pending in the conformance runner. |

## Authoring

| # | Behavior | CE | EE | Status | Owner / next step |
|---|---|---|---|---|---|
| A1 | Build protocol | `BuildRequestV5`: project mode with `acceptance/build.json` | `BuildRequestV4`: one JSON transaction | `gap` | The largest gap. Owner: EE, [EE #86](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/86). |
| A2 | Result identity fields | `ce_version`, `ce_error` | `ee_version`, `ee_error` | `CE-extension` | Edition identity on purpose. A conformance case never compares these names. |
| A3 | CLI commands | `version schema capabilities capability reference compile decompile build lint dry-run run export-contract` | the same 12 commands | `identical` | `authoring --help`. |
| A4 | Focused schema names | 13, with compile/decompile requests and results, `ready_build`, `rejected_build`, `build_request_v5` | 7, with `build_request_v4` | `gap` | Follows A1. Owner: EE, [EE #87](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/87). |
| A5 | Lint rule codes | 40 numbered `DM` codes plus build rule ids | 18 published rule entries, no `DM` codes | `gap` | Owner: EE, [EE #88](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/88). |
| A6 | Bounded execution of `clear` and `drop` | skip with `not_executed` warning | not specified | `unverified` | Needs the destructive-operations port to EE first. |
| A7 | Bounded execution of a failed `<assert>` | `assert_failed` at the assert line; keeps the products that completed; `not_executed` for the other checks; message only when literal | the run error as a diagnostic, with the message; no products | `gap` | EE has no Build v5 (A1). Corpus: `tests_ce/scenarios/s21_assert_gate`. |

## Behavior cases

| Case | Area | CE | EE |
|---|---|---|---|
| `ok_seeded_generate` | runtime | pass | not run |
| `ok_clear_then_insert` | runtime | pass | not run |
| `error_key_two_value_sources` | error handling | pass (`E011/I605`) | not run |
| `error_missing_include` | error handling | pass (`I201`) | not run |
| `error_unsupported_operation` | error handling | pass (`I320`) | not run |
| `error_clear_with_count` | error handling | pass (`E014/I928`) | not run |
| `error_drop_on_rdbms` | error handling | pass (`E014/I928`) | not run |
| `error_delete_whole_source` | error handling | pass (`E014/I928`) | known difference: EE 4.x rewrites to clear (`W003`) |

## Open rows

These rows are not compared yet. They need a comparison before the release date. Issue #401.

| # | Behavior | Why it is open |
|---|---|---|
| O1 | Typed error classes and their hierarchy | Not compared. |
| O2 | Redaction of host paths in diagnostics | CE redacts. EE not checked. |
| O3 | `W` warning codes: CE has `W002` and `W007` (`W008` is in #390), EE has `W001` to `W008` | The shared ones have the same name and title. Their runtime conditions are not compared. |
| O4 | Worker prefixes of multi-process runs | Needs a multi-process run in both editions. |
| O5 | Include and project contract (`acceptance/build.json`, literal includes) | Depends on A1. |
| O6 | Memstore form `<memstore id="mem"/>` (#382) | EE adoption not checked here. |
| O7 | Row-condition grammar | Not compared. |
| O8 | DM JSON compile and decompile output | Compare after A1. |
| O9 | Diagnostics envelope fields (`phase`, `path`, `remediation`) | Not compared. |

## Count

| Status | Rows |
|---|---|
| `identical` | 10 |
| `CE-extension` | 3 |
| `EE-only` | 4 |
| `gap` | 9 |
| `unverified` | 1 |
| Open rows (not compared) | 9 |
