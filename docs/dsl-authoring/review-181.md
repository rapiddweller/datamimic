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
   item or wrong structure` (`datamimic_ce/contexts/context.py:151`), which does
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
2. **Engine scope errors should name the identifier.** `'expr' have undefined
   item or wrong structure` should become `name 'account_no' is not defined in
   this scope; record-local names need this.`. File:
   `datamimic_ce/contexts/context.py` (evaluate_python_expression).
3. **Lint rule for per-parent increment ids.** Flag
   `generator="IncrementGenerator"` on an id-like key inside a nested
   `<generate>` with a hint to the composite-key pattern. File:
   `authoring/rules/best_practice.py`.
4. **Variable + literal generator combination** parses but yields nothing (see
   above). Wire it or reject it.
5. **Includes are linted flat.** `<include uri>` targets are not followed;
   multi-file descriptors get partial coverage. File: `authoring/linter.py`.
6. **`{script}` counts are uncappable in dry-run** (documented; timeout is the
   backstop). Subprocess isolation would also free the dry-run from the
   in-process GIL/timeout limitation.

## Verification trail

- Full suites: `pytest tests_ce/unit_tests/test_authoring tests_ce/unit_tests/test_showcase
  tests_ce/unit_tests/test_exporter tests_ce/unit_tests/test_mcp` (204 passed).
- All four showcase descriptors executed for real via `datamimic run` and their
  invariants (FK integrity incl. two-hop, join correctness, decision bands,
  custom components, determinism across two runs) verified against the produced
  JSON files, then pinned in CI (`tests_ce/unit_tests/test_showcase/`).
- `mypy datamimic_ce`: clean except two pre-existing `ray` import stubs
  (untouched files, optional dependency absent in the dev venv).
