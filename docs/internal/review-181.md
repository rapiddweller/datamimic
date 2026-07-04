# Review: PR #181 (Feat/dsl authoring), commit 932acf0

A critique of the merged DSL-authoring toolset, anchored in files and verified by
building four real end-to-end descriptors against it (`examples/showcase/`).
Every claim below was exercised, not inferred. Improvements marked IMPLEMENTED
shipped together with this review; the rest are sharp, scoped issues.

## Scope note: CE, not EE

The task brief referenced `datamimic_ee/model/element_registry.py`,
`get_lsp_schema()`, autocomplete drift tests, and `{expr}` vs `{{expr}}`
setup-time semantics. None of these exist in this repository. They are
Enterprise Edition surfaces. The CE equivalents, and what this review is
grounded in, are:

- element/attribute schema: `datamimic_ce/authoring/schema.py` (ELEMENT_MODEL_MAP
  plus pydantic `model_fields`, gate-tested against the parser in
  `tests_ce/unit_tests/test_authoring/test_schema_index.py`)
- capability enumeration: `datamimic_ce/authoring/reference.py` (registries,
  entities, generators) and now `datamimic capabilities` (CLI JSON)
- there is no LSP/autocomplete in CE; agents author from the reference tools,
  which is exactly the scenario PR #181 targets

## What #181 actually makes easier

- **Aggregated, hinted diagnostics.** `DescriptorLinter`
  (`datamimic_ce/authoring/linter.py`) walks all rules and returns every finding
  with a rule id and a non-empty `fix_hint` (gate-tested). The engine parser
  alone fails on the first error with free-text. Measured effect during
  development: a capable small model (Haiku 4.5) authored 6/6 intent-correct
  descriptors through the reference -> check -> run loop, 4 of them first try.
- **Safe dry-run with samples.** `datamimic_ce/authoring/dryrun.py` caps counts,
  strips file/DB targets, keeps memstores (pipelines still work), and returns
  sample rows. This is the intent-verification step: validity is not
  correctness.
- **Registry-derived reference.** Elements, entities (23), generators (35),
  targets, distributions are enumerated from the live registries; gate tests
  block drift and EE-term leakage
  (`tests_ce/unit_tests/test_authoring/test_reference_and_recipes.py`).

## Where an author (human or agent) still had to guess

Building the showcase surfaced these. Each cost a failed run despite a clean
lint and a clean dry-run at small scale.

1. **The scope rule is the number one trap.** Inside a nested `<generate>`,
   record-local names need `this.`; bare names resolve only at the top level.
   The runtime error was `'parent.customer_id * 10 + account_no' have undefined
   item or wrong structure` (`datamimic_ce/contexts/context.py:192`), which does
   not name the undefined item, let alone the rule. Two of four showcase
   examples hit this. IMPLEMENTED: the DM002 hint for `have undefined` now
   teaches the `this.` / `parent.` / `root.` rule and the CSV-string cast
   (`datamimic_ce/authoring/dryrun.py`, `_RUNTIME_HINTS`). Remaining issue: the
   engine message itself should name the missing identifier.
2. **IncrementGenerator counts per parent, not globally.** Child ids collide
   silently across parents; small dry-runs look plausible, full runs produce
   duplicate keys. Even the shipped recipe had it: `relational-parent-child.xml`
   generated non-unique `order_id`. IMPLEMENTED: recipe fixed (composite key
   from parent id plus local sequence, now the documented pattern). Remaining
   issue: no lint rule flags a bare `generator="IncrementGenerator"` id key
   inside a nested `<generate>`; DM3xx candidate.
3. **Lint-clean, dry-run-clean, real run crashed.** `<key type="decimal">` with
   `target="JSON"` threw `Object of type Decimal is not JSON serializable` at
   export time. The dry-run cannot see export-layer failures because it strips
   the very targets that crash. IMPLEMENTED: `DateTimeEncoder` in
   `datamimic_ce/exporters/json_exporter.py` now serializes `Decimal` (float)
   and `date` (isoformat), tested in
   `tests_ce/unit_tests/test_exporter/test_json_encoder.py`. Remaining issue:
   the dry-run/real-run gap is structural; see issues below.
4. **Dry-run samples stringified nested structures.** `_clip_value`
   (`dryrun.py:219` pre-change) turned a nestedKey list into the string
   `"[{'rating': 3}]"`, so an agent could not programmatically verify shape.
   IMPLEMENTED: structure-preserving clipping (dict/list recurse, strings clip,
   other leaves stringify), tested in `test_dryrun.py`.
5. **`<variable generator="IncrementGenerator"/>` parses but never evaluates.**
   The model accepts `generator=` (`datamimic_ce/model/variable_model.py:58`),
   the parse passes, the value is undefined at script time. Cost one failed
   iteration. Remaining issue: either wire literal generators into variables or
   reject the combination at lint/parse time.
6. **No converter discoverability.** 13 built-in converters existed only as an
   inline dict in `TaskUtil.create_converter_list`
   (`datamimic_ce/tasks/task_util.py:270`); no reference topic listed them.
   IMPLEMENTED: `topic=converters` (from `ConverterEnum`, gate-tested) and the
   `datamimic capabilities` CLI manifest covering elements, attributes,
   generators, entities, converters, targets, distributions.

## The three highest-impact improvements

1. **Structure-preserving dry-run samples** (implemented). Problem: agents
   verify intent from samples; strings hide shape. Fix: recursive clip. Test:
   nestedKey list arrives as a list of dicts.
2. **Queryable capability manifest without MCP** (implemented). Problem: a
   coding agent in a plain shell has no discoverability; hand-written docs
   drift. Fix: `datamimic capabilities` emits JSON derived from the registries;
   `test_capabilities_manifest_matches_registries` pins it to the live code.
3. **Scope-teaching runtime hints** (implemented). Problem: the most common
   authoring failure produced the least helpful message. Fix: DM002 hint now
   states the rule. Test: `test_dm002_runtime_errors_carry_actionable_hints`.

## Issues left open, in priority order

1. **Dry-run cannot catch export-layer crashes** (targets are stripped by
   design). Proposal: an opt-in `smoke_export=true` that writes one batch per
   file exporter into a temp dir and deletes it; would have caught the Decimal
   crash. Files: `authoring/dryrun.py` (neutralizer), `mcp/models.py`.
   IMPLEMENTED: `smoke_export` on `dry_run()`/`dry_run_source()` and the
   `datamimic_run` MCP tool replays captured rows through each stripped FILE
   exporter (write + finalize) inside a TemporaryDirectory; a failure becomes a
   DM002 diagnostic naming the exporter. Console/Log and client targets are
   never smoked. Tested in `test_dryrun.py`, incl. the nested-product
   capture-key mapping and the no-artifacts guarantee.
2. **Engine scope errors should name the identifier.** `'expr' have undefined
   item or wrong structure` should become `name 'account_no' is not defined in
   this scope; record-local names need this.`. File:
   `datamimic_ce/contexts/context.py` (evaluate_python_expression).
   IMPLEMENTED: `SAFE_GLOBALS["__builtins__"]` is now `{}` (not `None`), so a
   missing name raises a real NameError instead of an opaque TypeError; the
   ValueError message names the identifier and appends the this./parent./root.
   scope guidance (exception type unchanged). AttributeError/KeyError from
   scripts name the missing member/key too.
3. **Lint rule for per-parent increment ids.** Flag
   `generator="IncrementGenerator"` on an id-like key inside a nested
   `<generate>` with a hint to the composite-key pattern. File:
   `authoring/rules/best_practice.py`.
   IMPLEMENTED as DM315 (WARNING), structural match only: a bare
   IncrementGenerator key whose nearest scope is a generate/iterate nested in
   another generate/iterate. Keys inside `<nestedKey>` and top-level generates
   stay silent. The local-sequence keys in shipped recipes/showcase carry the
   warning by design; it restates the composite-key pattern they already
   apply, and warnings do not gate lint ok.
4. **Variable + literal generator combination** parses but yields nothing (see
   above). Wire it or reject it.
   CORRECTION: the claim was wrong: `<variable generator="IncrementGenerator"/>`
   evaluates fine (same generator path as `<key>`); the observed failure was a
   bare record-local name inside a nested `<generate>` (`this.acc_seq` works;
   the scope rule from item 2). Regression-pinned in
   `test_dryrun.py::test_variable_literal_generator_evaluates_in_scripts`.
5. **Includes are linted flat.** `<include uri>` targets are not followed;
   multi-file descriptors get partial coverage. File: `authoring/linter.py`.
6. **`{script}` counts are uncappable in dry-run** (documented; timeout is the
   backstop). Subprocess isolation would also free the dry-run from the
   in-process GIL/timeout limitation.

## The falsifiable test

Definition of done for agent legibility: a fresh coding agent, given only the
instruction "generate a realistic multi-table banking dataset with referential
integrity" and this repository, must succeed from the repo's own docs and
examples. Run on 2026-07-04 with a small model (Haiku 4.5), no other guidance.

Result: PASS. The agent produced a seeded six-table descriptor (customers,
accounts, transactions, account holders, statements, disputes) using the
memstore-pipeline and script-FK-carry patterns from AGENTS.md and the showcase.
Independent verification of its CSVs (not its self-report): unique keys, all
FKs resolve, and relationship-level integrity holds, including
transaction.customer_id == owner(transaction.account_id) two-hop and the
dispute -> transaction -> account -> customer three-hop chain. Zero violations.

Two gaps the test surfaced, kept honest:

- The agent wrote `count="150"` (and 1200, 300) on source-driven generates over
  a 50-row source without `cyclic`; the engine silently capped every table at
  50 rows and the agent misattributed the cause to pagination. New issue 7
  below.
- Its self-report inflated ("251 records", "~2300 estimated"); the data was
  right, the narrative was not. Independent verification of outputs remains
  mandatory.

## Issues left open (continued)

7. **`count=` above source length caps silently without `cyclic`.** A
   source-driven `<generate count="1200">` over 50 source rows yields 50 rows
   and no warning. Lint cannot know source length; the dry-run caps counts
   itself, so the underrun only shows at real scale. Best fix: an engine-level
   warning when a source exhausts below an explicit count, plus a
   DM3xx hint when `count=` is combined with `source=` and no
   `cyclic`/`distribution`. Files: `datamimic_ce/tasks/generate_task.py`,
   `authoring/rules/best_practice.py`.
   IMPLEMENTED, both halves: DM316 (HINT) fires on `source=` + literal digit
   `count=` without `cyclic="True"` (cumulated excluded: with-replacement
   never runs out); and `GenerateTask._warn_count_above_source` logs one
   warning per top-level statement naming the statement, requested count and
   actual source rows when the non-cyclic read would cap.

## Verification trail

- Full suites: `pytest tests_ce/unit_tests/test_authoring tests_ce/unit_tests/test_showcase
  tests_ce/unit_tests/test_exporter tests_ce/unit_tests/test_mcp` (210 passed at the time of the accuracy re-review).
- All four showcase descriptors executed for real via `datamimic run` and their
  invariants (FK integrity incl. two-hop, join correctness, decision bands,
  custom components, determinism across two runs) verified against the produced
  JSON files, then pinned in CI (`tests_ce/unit_tests/test_showcase/`).
- `mypy datamimic_ce`: clean except two pre-existing `ray` import stubs
  (untouched files, optional dependency absent in the dev venv).
