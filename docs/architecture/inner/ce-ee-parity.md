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
| E1 | Issue code names and values | 115 codes (105 at `10ac45a9`, then `W008`, `I196`, `I197`, `I198`, `I199`, `I200`, `I209`, `I438`, `I439`, `I956`) | 411 codes. 104 of the 105 CE codes at `10ac45a9` have the same name and value. | `gap` | `TASK_TOTAL_ROW_BUDGET_EXCEEDED` (`I955`) exists only in CE. Reserve it in EE first (CE rule: CE codes are a subset of EE). Owner: EE session, then CE. Issue #400. Rows E1a to E1i list the codes added after `10ac45a9`; `W008` is in O3. |
| E1a | `SOURCE_SELECTOR_BLANK` (`I196`): blank `selector` or `iterationSelector` on a database source (#397) | present | not defined (EE uses up to `I195`) | `gap` | Owner: EE reservation. Reserve `I196` with the same name in EE. |
| E1b | `SOURCE_INVALID_XLSX` (`I197`): file is not an `.xlsx` workbook (#379) | present | not defined | `gap` | Owner: EE reservation. Reserve `I197` with the same name in EE. |
| E1c | `SOURCE_INVALID_FIXED_WIDTH` (`I198`): `.fcw` file without a valid spec line (#379) | present | not defined | `gap` | Owner: EE reservation. Reserve `I198` with the same name in EE. |
| E1d | `GENERATE_ROW_SELECTION_FILE_ONLY` (`I199`): `where=`/`columns=` on a memstore or database source (#447) | present | not defined | `gap` | Owner: EE port, [EE #93](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/93). Reserve `I199` with the same name and template. `I199` is the last number of the EE `I1xx` source range; the later source codes `I200` and `I209` fall into the `I2xx` include range (E1e, E1f). |
| E1e | `GENERATE_ROW_SELECTION_SOURCE_SCRIPTED` (`I200`): `where=`/`columns=` with `sourceScripted` (#447) | present | not defined | `gap` | Owner: EE port, [EE #93](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/93). Reserve `I200` with the same name and template. `I200` is a source code inside the `I2xx` include range of EE; reserve it in EE #93 with the family exception noted. |
| E1f | `SOURCE_COLUMN_UNKNOWN` (`I209`): a `columns=` name that no source row has (#447) | present | not defined (EE uses `I201` to `I208`) | `gap` | Owner: EE port, [EE #93](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/93). Reserve `I209` with the same name and template. `I209` is a source code inside the `I2xx` include range, and it is the next free EE include number: reserve it in EE #93 before EE adds an include code. |
| E1g | `GENERATOR_ARGUMENT_UNKNOWN` (`I438`): a key, variable or element attribute that its generator does not take (#456, #460) | present; the template names the element tag (`<{element_tag}> '{element_name}'`) and the attribute as written | not defined (EE uses `I401` to `I437`) | `gap` | Owner: EE port, [EE #95](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/95) and the #460 EE ticket (A11). Reserve `I438` with the same name and template. It is the next free number of the generator range in both editions. |
| E1h | `GENERATOR_ARGUMENTS_IN_TWO_FORMS` (`I439`): a generator call and argument attributes on one key, variable or element (#456, #460) | present; the template names the element tag | not defined | `gap` | Owner: EE port, [EE #95](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/95) and the #460 EE ticket (A11). Reserve `I439` with the same name and template. |
| E1i | `TASK_EXPRESSION_BUILTIN_UNAVAILABLE` (`I956`): a script calls a Python builtin that scripts do not offer, such as `open`, `next` or `isinstance` (e07 campaign); a bare builtin name that no field holds (such as an ancestor `id`) stays `I832` | present; the message names the builtin (a closed set, no descriptor value) and lists the offered builtins; before, the same script failed with `I832` and the scope hint | `I832` with the name in the message | `gap` | Owner: EE port, [EE #105](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/105). Reserve `I956` with the same name and template (`I833` is `TASK_COMMON_SUBTASK_INVALID` in EE; `I956` is the next number free in both editions). Acceptance: the `s31_file_lookup` negatives `a_script_cannot_open_a_file` and `next_is_no_script_builtin` pass on EE. |
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
| E13 | JSON source with `NaN`, `Infinity`, `-Infinity` or a number above the largest float | read as a float | read as a float: `FileUtil.read_json` uses `json.load` (EE `5d19c9687`, code check, no run) | `identical` | Decision (#379, owner): both editions accept these values; a catalog code for them is left out by decision. CE's JSON exporter writes `NaN`, and CE reads that file back (`test_a_json_file_that_ce_exports_with_nan_reads_back`). CE `authoring dry-run` and Build still refuse a non-finite captured value with `child_execution` and no catalog code, as on `development` before #379. |

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
| A8 | `where=` and `columns=` on `<generate>`/`<iterate>` file sources (#447) | row condition over one row before count, cyclic, distribution, paging and chunks; clock reads and random draws refused; output column list, unlisted columns stay row variables; Build counts kept rows in its bounded run | not ported: no `where`/`columns` on the generate model | `gap` | Owner: EE port, [EE #93](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/93). Apply the condition in every file loader and every length counter before the count (CSV counter, JSON/NDJSON streaming; no parquet metadata count with `where`). Acceptance: CE scenario `tests_ce/scenarios/s22_file_filter` and `tests_ce/integration_tests/test_file_filter` pass on EE. |
| A9 | Natural spellings of first-Build input (#426) | `range` accepts `min`/`max`; `result_type: "boolean"`; `values="A,B,C"` (two or more plain ASCII names, no keyword) reads as strings in Build and in `datamimic run`; the published schema lists the range spellings | `range` takes `minimum`/`maximum` only; `result_type` takes `"bool"` only; `values=` takes a Python literal (`literal_eval`) only | `gap` | Owner: EE port, with [EE #86](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/86). A CE project that uses a bare `values=` list fails in EE (`key_variable_task.py` line 227). Conformance case to add: `ok_values_plain_names`. |
| A10 | Generator arguments as key attributes (#456) | `<key generator="IntegerGenerator" min="18" max="65"/>` builds the call `IntegerGenerator(min=18, max=65)`; `min`, `max` and `granularity` go to the generator when its constructor takes them; same rows as the call form for one seed; `I438`; `I439` refuses a call form (even `IntegerGenerator()`) together with any argument attribute, not only the same argument in both; `distribution` next to `generator=` is refused (`DM218`); `minLength`/`maxLength` are the `min_len`/`max_len` arguments (#459) and need `type=` or `generator=` (`DM214`/`DM218`, `DM220` without `generator=` unless `type="string"`/`"binary"`); the numeric `type=` gates (`DM220`) do not apply next to `generator=` (#458, `AllowedValuesWhen.unless`) | refuses `min`/`max`/`granularity` next to `generator=`; ignores `minLength`/`maxLength` next to `generator=` | `gap` | Owner: EE port, [EE #95](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/95); #458 and #459 are in the #460 EE ticket (A11). A CE project that uses the attribute form fails in EE. Acceptance: CE scenario `tests_ce/scenarios/s26_key_generator_attributes` (9 equivalents, 25 negatives) passes on EE. |
| A11 | Generator arguments as variable and element attributes (#460) | `<variable>` and `<element>` take `min`, `max`, `granularity`, `minLength`, `maxLength` as `generator=` arguments, as `<key>` does (A10), except that `distribution=` beside `generator=` is not yet refused on `<variable>` (CE #468); on `<variable>` each needs `generator=` (`DM214`) | `<variable>` refuses the attributes; EE `<element>` not compared | `gap` | Owner: EE port, EE ticket [#96](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/96) (covers CE #458, #459, #460). A CE project that uses the form fails in EE. Acceptance: CE scenario `tests_ce/scenarios/s27_variable_generator_attributes` (6 equivalents, 16 negatives) passes on EE. |
| A12 | Seeded random stream of an included step (#463) | the entry keeps `Random(rngSeed)`; each run of an included step draws from a stream keyed by the seed and the step key (parent key, include path relative to the project root, run number); the same step twice, an include inside a `<generate>` and a nested step from two parents each get their own stream; step order and project directory do not change the rows | keys draws by `<generate>` names (`RngContext.statement_path`); an include keeps the root `RngContext`. Static reading only, not run: the EE venv native module is older than the source | `gap` | Owner: EE port, [EE #97](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/97). Expected EE collisions: a step run twice, an include inside a `<generate>`, two steps with a generate of the same name. Acceptance: CE scenario `tests_ce/scenarios/s29_included_step_streams` and `tests_ce/integration_tests/test_included_step_seed` pass on EE (properties, not CE row values). |
| A13 | Remediation of the first rejections that cost blind agents the most Builds (b3 campaign, e06 and e07) | the unread-memstore rejection names its three routes with the product and store names: nest for a subset (with `max_count` for the braces count), a `storage="data"` variable for a file lookup (remove the `<memstore>` and its writer), a `sourceEntity` readback with `target="ConsoleExporter"` and the role pair for a copy; one rule text (`MEMSTORE_READBACK_ONCE`) for all three memstore rejections; `I955` names the top-level `max_count` key of `acceptance/build.json`, the ceiling and `"max_count": 2000` for an unknown total; `DM212` shows both count forms and that a braces count needs `max_count`; the `<memstore id>` description teaches the `<generate>` readback; the `memstore` reference example uses `mem` | not compared: EE has no `DM` codes (A5), no `I955` (E1) and Build v4 (A1) | `gap` | Owner: EE, after A1 and A5: [EE #104](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/104). Conformance case: `tests_ce/scenarios/s30_memstore_readback_routes` (10 negatives, 8 of them check the remediation text; 2 equivalents). |
| A14 | Teaching the file lookup (a join of a second file, campaign b3 case e07) | the learning entry `lookup` (scenario `s31_file_lookup`); `DM103` for `where` on `<variable>`/`<nestedKey>` gives the lookup; a `where=` name failure (`parent.`, `root.`, a variable) says that `where=` reads one row, in the run message and in Build (`I832` stays) | no `lookup` reference, no `DM` codes (A5), no `where=` (A8) | `gap` | Owner: EE port, [EE #105](https://gitlab.dwellerlab.com/rapiddweller/datamimic/datamimic-ee/-/work_items/105). The `storage="data"` lookup itself runs in both editions (not run in EE here). Acceptance: CE scenario `tests_ce/scenarios/s31_file_lookup` passes on EE once A8 is ported. |

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
| `identical` | 11 |
| `CE-extension` | 3 |
| `EE-only` | 4 |
| `gap` | 26 |
| `unverified` | 1 |
| Open rows (not compared) | 9 |
