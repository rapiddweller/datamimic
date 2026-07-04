# DSL authoring benchmark

Compares how well local (Ollama) models write DATAMIMIC DSL descriptors under
different amounts of prompt guidance. The axis under test is the prompt, not
the model: same task text, four levels of DSL context, scored with the repo's
own linter and dry-run engine instead of a human or an LLM judge.

## Run it

```
. .venv/bin/activate  # or use .venv/bin/python directly
python benchmarks/dsl-authoring/bench.py --selftest   # validate the intent checks, no Ollama calls
python benchmarks/dsl-authoring/bench.py --smoke      # 1 cell: gemma4:31b / P1_intent_table / weighted_country
python benchmarks/dsl-authoring/bench.py              # full matrix: DEFAULT_MODELS x all variants x all tasks
```

Filter a run:

```
python benchmarks/dsl-authoring/bench.py --models qwen2.5:7b --variants P0_bare P2_cheatsheet --tasks weighted_country timeseries
```

Ollama must be running locally (`http://localhost:11434`) with the target
models pulled (`ollama pull <model>`). Each cell is one `/api/chat` call:
`stream: false`, `think: false` (required for thinking models like
`gemma4:31b`; harmless no-op on the rest), `temperature 0.2`,
`num_predict 1400`, `num_ctx 8192` (P2/P3 prompts run past Ollama's default
2048/4096 context; without raising it the cheatsheet/recipe gets silently
truncated and the comparison is confounded), 300s timeout per call.

Output:
- `results/<timestamp>.json` (or `--out <path>`): every cell, written after
  each call so a crash mid-run does not lose earlier results.
- `results/latest.md`: the markdown report from the most recent run.
- stdout: the same markdown report.

## Scoring

Each generation goes through three gates, in order:

1. **Extract** the first `<setup ...>...</setup>` block from the reply
   (models wrap XML in markdown fences; the block is found by locating
   `<setup` directly, fences are irrelevant). If the reply was cut off before
   `</setup>`, a closing tag is appended. No `<setup` at all -> score 0
   (`rule_ids: ["NO_XML"]`).
2. **Lint** (`datamimic_ce.authoring.lint_source`). Any ERROR diagnostic ->
   score 0, `rule_ids` = the failing rule ids (e.g. `DM104`).
3. **Dry-run** (`datamimic_ce.authoring.dryrun.dry_run_source`,
   `sample_rows=60, max_count=60`). A failed run, or a run producing 0 rows
   -> score 0, `rule_ids` = the dry-run diagnostic rule ids (`DM002`
   runtime error, `DM004` empty output).

If all three gates pass, a per-task **intent check** runs against the
`DryRunResult` products (real sample rows, structure preserved: lists of
dicts stay lists of dicts). It matches fields by case-insensitive substring,
not exact name, since the model picks its own field names:

- pass -> **score 2**
- fail -> **score 1** (the descriptor lints and runs, but doesn't do what was
  asked: e.g. a `country` value outside the fixed set, a `doubled` field
  that isn't `2 * value`, a customer's `city` that doesn't match its
  branch's)

Two task shapes (`branch_fk`, and implicitly any parent/child task) accept
more than one valid descriptor structure: a flat pair of products joined by
id, or a single product with an embedded `<nestedKey type="list">` of
children carrying the parent's fields. The intent check tries the nested
shape first, falls back to the flat one, and fails either way if the copied
values are wrong.

Run `bench.py --selftest` to check the intent checks themselves against one
hand-written, known-good descriptor per task (`GOLDEN_DESCRIPTORS` in
`bench.py`): it must print `score=2` for every one. Do this after touching
any intent check, before spending GPU time on a real matrix run.

## Task set (fixed ids)

`weighted_country`, `nested_reviews`, `reproducible_orders`,
`memstore_pipeline`, `timeseries`, `branch_fk`: see `TASKS` in `bench.py`
for the exact prompt text and intent check per task. Ids are fixed: another
run (e.g. a different model track) can reuse the same set for a comparable
result.

## Prompt variants (the benchmark axis)

- `P0_bare`: task text only.
- `P1_intent_table`: P0 plus a value-source mapping table (which DSL
  attribute to use for a fixed set of options, a number range, a real name,
  a unique id, a coded string, a nested list, reproducibility, a memstore
  pipeline, a time series, a parent/child join).
- `P2_cheatsheet`: P0 plus the full agent cheatsheet
  (`datamimic_ce.authoring.reference.reference("overview")`).
- `P3_fewshot`: P0 plus one complete worked example (the
  `relational-parent-child` recipe XML).

## Adding a model

Add the Ollama model name to `--models` (or `DEFAULT_MODELS` in `bench.py`).
Pull it first (`ollama pull <name>`). No code change needed.

## Adding a prompt variant

Add a function `task_prompt -> str` to `PROMPT_VARIANTS` in `bench.py`. It
receives the raw task prompt text; call `_p0(task_prompt)` internally to
keep the "output only the XML" instruction consistent across variants.

## Adding a task

Add an entry to `TASKS` in `bench.py`: `id`, `prompt` (the text sent to the
model), `intent_check` (a `(xml: str, result: DryRunResult) -> bool`
callable). Then add one hand-written golden descriptor for it to
`GOLDEN_DESCRIPTORS` and confirm `--selftest` scores it 2 before running it
against any model. Match fields by substring, not exact name: the model
picks its own naming.

## Known harness limitations

- Intent checks match fields by substring (`"branch" in key.lower()`), so a
  model that names a field just `id` instead of `branch_id` can fail the
  `branch_fk` check even if the join itself is correct. This is deliberately
  narrow rather than guessing at arbitrary field names.
- `memstore_pipeline`'s check looks for any product with both a `value`-ish
  and a `doubled`-ish key; a field literally named e.g. `doubled_value`
  would match `find_key(row, "value")` first due to substring order and
  give a false pairing. Not observed in practice, but possible.
- `nested_reviews`' check is intentionally an existence check ("some
  rating in 1-5 exists somewhere in a nested list"), not a bounds check
  over every rating in every row: matching the stated task intent, not a
  stricter one.
- Scoring assumes each Ollama call's `message.content` is the entire reply;
  a model that streams reasoning into `content` instead of respecting
  `think: false` would inflate token count without changing the
  extraction/lint/dry-run logic (unaffected in testing, since gemma4:31b was
  verified to omit its thinking trace when `think: false` is set).
