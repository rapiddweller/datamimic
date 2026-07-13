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
python benchmarks/dsl-authoring/bench.py --models gemma4:12b --variants P0_bare P2_cheatsheet --tasks weighted_country timeseries
```

Add `--think` to a `--loop` run to enable Ollama's thinking mode (off by
default — see "Known harness limitations").

Ollama must be running locally (`http://localhost:11434`) with the target
models pulled (`ollama pull <model>`). Each cell is one `/api/chat` call:
`stream: false`, `think: false` unless `--think` is passed (required
`false` for `gemma4:31b` to respond at all when thinking is off; verified
harmless there — NOT verified harmless on other thinking-capable models, see
"Known harness limitations"), `temperature 1.0, top_p 0.95, top_k 64` (Gemma
4's own documented recommendation — the roster is Gemma-only, see "Local
model selection"), `seed 42` (fixed so repeated runs of the same model+task
are reproducible instead of a fresh sample each time), `num_predict 1400`,
`num_ctx 8192` (P2/P3 prompts run past Ollama's default 2048/4096 context;
without raising it the cheatsheet/recipe gets silently truncated and the
comparison is confounded), 300s timeout per call.

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

## Loop condition (the agentic comparison)

```
python benchmarks/dsl-authoring/bench.py --loop                          # all DEFAULT_MODELS, all tasks
python benchmarks/dsl-authoring/bench.py --loop --models qwen2.5:7b --tasks branch_fk
```

Local models here have no native function calling, so the harness plays the
agent loop for them: the model only ever sees chat messages, the harness runs
the tools and feeds the results back.

- Initial prompt: `P2_cheatsheet` (closest to what an agent gets from the
  reference tool).
- After each generation the harness extracts the XML and evaluates it. If it
  is not intent-correct, the model gets a feedback message and one more try:
  - lint errors: a compact diagnostics block (`- [rule] message | fix: hint`,
    capped at 12 findings) plus the model's previous XML.
  - lint clean but dry-run fails or 0 rows: the dry-run diagnostics, same
    format.
  - runs but intent check fails: one line restating the task intent
    (`intent_text` in `TASKS`) plus the first generated sample row.

  Every feedback ends with: return a corrected COMPLETE descriptor, output
  only the XML.
- Max 3 generations per task. The cell score is the score of the LAST
  generation (0/1/2 as in the static conditions); `iterations` and
  per-iteration score/rule ids/latency are recorded in the results JSON.
- The conversation is multi-turn: the cheatsheet stays in context, each
  attempt appends the assistant reply and the feedback. `num_ctx` is raised
  to 16384 for loop calls.
- Timeouts: a timeout before any generation marks the cell `timeout`; after
  at least one generation, the last completed generation is scored and the
  timeout noted. Two consecutive timed-out cells skip the model's remaining
  cells.

Loop results are written to `results/<timestamp>-loop.json`. To produce a
combined `results/latest.md` with the loop column next to the static
variants:

```
python benchmarks/dsl-authoring/bench.py --report results/<static>.json results/<loop>.json
```

The combined report adds, per model, a static-best vs loop comparison line
and a loop-iterations histogram, plus a reference line to the Haiku track
figures (`results/haiku-track-20260704.md`).

## Adding a model

Add the Ollama model name to `--models` (or `DEFAULT_MODELS` in `bench.py`).
Pull it first (`ollama pull <name>`). No code change needed.

## Local model selection

Prefer models that report both `tools` and `thinking` in `ollama show <model>`'s
Capabilities block. `tools` is not exercised by the harness today (see "Known
harness limitations") — this is a forward-looking criterion, not a claim the
current `--loop` condition uses it: `tools` support is what would let a
future harness condition drive real MCP tool calls instead of the manual
lint/dry-run text loop (a more realistic test of "can this model run as an
agent against our MCP server," not just "can it write XML from feedback").

`thinking` support is now testable: `--think` enables it (off by default,
`--loop` only). Verified 2026-07-13 against a live Ollama call that `content`
and `thinking` are separate JSON fields in the response regardless of the
flag — the harness only ever reads `content`, so message history built from
it already complies with Gemma 4's own documented multi-turn rule ("no
thinking content in history") whether `--think` is on or off; this was a
real risk worth checking, not a given. Gemma 4's own docs note one asymmetry
worth re-testing once `gemma4:e4b` is available locally: disabling thinking
on the dense/MoE sizes still emits an empty thought-channel wrapper around
the answer, but the E2B/E4B variants are documented to behave differently —
unverified whether `think: false` is fully clean on `gemma4:e4b` the way it
is on `gemma4:31b`.

As of 2026-07-13 the roster is Gemma-only (`gemma4:12b`, `gemma4:26b`,
`gemma4:31b`, `gemma4:e4b`) after `gemma4:31b` clearly outperformed every
other locally-available model on this task set (6/6 intent-correct under the
loop condition, matching Haiku 4.5). Non-Gemma models were removed from local
Ollama storage rather than just dropped from `DEFAULT_MODELS`, to keep the
local model zoo aligned with what's actually still worth benchmarking here.

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
  and a `doubled`-ish key; a single field like `doubled_value` matches both
  substrings, and the check skips that row (`dk == vk` guard) rather than
  pairing a field with itself. A model whose only numeric fields collide
  this way therefore scores 1, not a false 2.
- `nested_reviews`' check is intentionally an existence check ("some
  rating in 1-5 exists somewhere in a nested list"), not a bounds check
  over every rating in every row: matching the stated task intent, not a
  stricter one.
- Scoring assumes each Ollama call's `message.content` is the entire reply
  and never includes reasoning tokens. Confirmed 2026-07-13 by direct
  `/api/chat` calls to `gemma4:31b`: `thinking` is always a separate JSON
  field, never merged into `content`, with or without `--think`.
- `--think` (default off) threads through `call_ollama`/`run_loop_cell`/
  `run_loop_matrix` to enable thinking mode, but no A/B run has been done
  yet — thinking's effect on this specific task (structured XML generation
  with lint/dry-run feedback, not open-ended reasoning) is unverified in
  either direction. Cost is real: ~4x latency observed on a trivial prompt
  against `gemma4:31b` (local test, contended with concurrent downloads —
  treat as directional, not a clean measurement).
- The `--loop` condition never uses native tool-calling (Ollama's `tools=`
  chat parameter) even for models that support it — it always drives the
  manual "generate XML, lint/dry-run, feed diagnostics back as a chat
  message" loop. A model's `tools` capability flag is not exercised by
  anything in this file today.
