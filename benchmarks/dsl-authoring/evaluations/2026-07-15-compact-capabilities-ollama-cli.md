# Compact `capabilities` + local Ollama CLI-only authoring diagnostic — 2026-07-15

This is a single-seed diagnostic against `feat/capabilities-compact-index`
(PR #215), evaluated with a throwaway, uncommitted harness. It is not a
portable benchmark suite, a model ranking, or a reliability claim. Raw model
transcripts, provider request identifiers, and runtime evidence are
intentionally not tracked — only this curated record.

## Goal

PR #215 makes `datamimic capabilities` return a compact, versioned index by
default (~10x smaller than the full manifest) instead of an unbounded dump,
with `--full`/`--section` as drill-down. The question this diagnostic answers:
**is the compact index, together with the CLI's other discovery commands,
still sufficient for a small local model to author a verified `model.dm.json`
using only the `datamimic` CLI as its tool?** This is the actual use case the
`capabilities` command exists for.

## Contract and method

Isolation was enforced structurally, not just by prompt: the harness
(`ollama_cli_eval.py`, throwaway, not committed) never imports `datamimic_ce`.
Every DATAMIMIC interaction is a `subprocess` call to the installed
`.venv/bin/datamimic` console script, restricted to an allow-list of
subcommands (`--help`, `capabilities`, `reference`, `scaffold`, `lint`,
`dry-run`). The model's only knowledge of DATAMIMIC is what those commands
return in-conversation; it has no access to repository source, tests, or
documentation.

Each model got a system prompt naming the CLI as its only tool, listing the
exact allowed invocation forms (including `reference authoring`, `reference
authoring --category <category> --kind <kind>`, and `reference scaffold`), and
a submission protocol: reply with one `CLI: <args>` line, or a fenced
` ```json ` block containing the final `model.dm.json`. Every reply was fed
back either as a CLI result or as the structured `scaffold --format json`
issue list. Budget: 6 turns total per model, seed 42, temperature 0.2.

**Task (T1 flat, reused from a prior — since-deleted — diagnostic; a
proven, already-specified task, no new design needed):** generate exactly 5
records for a product named `records`, each with a globally unique integer
`id`, a `category` in exactly `{"A","B","C"}`, and an integer `score` in
`[10, 20]`.

**Typed oracle:** independent of what the model itself declares. Given
`scaffold`'s raw sample rows, the harness checks (not the model's
self-reported `verified` flag alone): exactly 5 rows, `truncated_rows=false`,
all `id`s distinct integers, all `category`s in the domain, all `score`s in
range, and `scaffold`'s own `verified` flag is `true`. A hand-built gold
`model.dm.json` for this task was verified against `scaffold
--smoke-export --deterministic-replay` before any model ran, confirming the
task is achievable and the oracle is well-formed (`verified=true`, 4/4
acceptance checks passed, deterministic replay passed).

## Access gate

| Model | Local | Access |
|---|---|---|
| `qwen3.5:9b-mlx` | yes (MLX) | pass |
| `gemma4:e4b` | yes | pass |
| `gemma4:e4b-it-qat` | yes | pass |

All three models were reachable via the local Ollama server; no access
failures. `-cloud`-tagged Ollama models were excluded — they proxy to Ollama's
cloud, not local inference, and were out of scope for this "local model" test.

## Reproduction chain (as actually executed)

```text
system prompt: CLI is the only tool, allowed invocations listed
  -> business intent (T1 flat) as the first user turn
  -> model replies with either "CLI: <args>" or a ```json``` model.dm.json
  -> CLI: subprocess call to datamimic, stdout/stderr fed back verbatim
  -> ```json```: datamimic scaffold - --format json --smoke-export --deterministic-replay
  -> typed oracle over scaffold's raw sample rows + verified flag
  -> on failure, the structured issue list is fed back as the next turn
  -> stop on oracle pass, or after 6 turns
```

## Per-model result

| Model | CLI discovery calls | `scaffold` submissions | Turn reached `verified=true` | Outcome |
|---|---|---|---|---|
| `qwen3.5:9b-mlx` | 0 | 6 | — | fail: turn budget exhausted |
| `gemma4:e4b` | 1 (`capabilities`) | 5 | — | fail: turn budget exhausted |
| `gemma4:e4b-it-qat` | 1 (`capabilities`) | 5 | — | fail: turn budget exhausted |

**0/3 verified within budget.** None of the three models called `reference
authoring` or `reference scaffold` at any point, despite both being explicitly
named as available in the system prompt — all three went straight from at
most one `capabilities` call to guessing a `model.dm.json` shape from
scratch, and never queried the typed field/product schema that would have
told them the exact required keys.

- **`qwen3.5:9b-mlx`** never called `capabilities` or `reference` at all —
  turn 1 was already a (wrong) `model.dm.json` guess using invented top-level
  keys (`product`, `type: "integer"`, `unique: true`, none of which exist in
  `AuthoringSpecV1`). After the turn-2 correction attempt still failed
  (`products` must be a non-empty tuple), turns 3–6 resubmitted the **exact
  same** `{"products": [], "seed": 42, "version": "1"}` payload four times
  in a row, ignoring the repeated identical feedback — a genuine stuck loop,
  not a convergence attempt.
- **`gemma4:e4b`** called `capabilities` once (turn 1), then spent turns 2–6
  iterating: `missing_field`/`unknown_field` (wrong top-level shape) →
  `constraint_violation` (`version` needed as the string `"1"`, `products`
  needed to be a tuple) → `invalid_discriminator` (used `products` as a
  dict, then as an array of dicts missing the required `kind` field). It was
  still failing discriminator validation at turn 6, one structural fix away
  from a submittable shape but out of budget.
- **`gemma4:e4b-it-qat`** followed the same general trajectory, and came
  closest to a pass: by turn 5 it corrected the product discriminator to the
  literal `"kind": "generated"` (the exact enum member) after seeing the
  engine's own list of valid tags in the previous turn's diagnostic. At turn
  6, the only remaining issues were a missing `count` field and one stray
  `unknown_field` (`generate`, left over from an earlier guess) — this run
  was visibly converging turn over turn and plausibly would have reached
  `verified=true` within 1–2 more turns.

Total wall-clock spent inside `scaffold` calls per model was small (2.9–3.7 s
across 5–6 calls each) — the bottleneck was authoring correctness, not CLI or
model latency.

## Decision

- **NO-GO:** unguided CLI-only authoring (discovery left optional in the
  prompt, no mandatory `reference` step) by small local models within a
  6-turn budget. 0/3 verified on the simplest possible task (T1 flat).
- **NO DATA:** whether the compact `capabilities` index itself is the
  bottleneck, versus the models simply not using the `reference` discovery
  commands that were offered. Two of three models fetched `capabilities`
  once; none progressed to `reference authoring`, which is what actually
  carries the exact required-field list. This diagnostic cannot separate "the
  compact index wasn't enough" from "the models never asked for the next
  level of detail" — both were true here, but the second explains the
  failures at least as well as the first.
- **NO DATA:** model ranking or reliability claims from a single seed and a
  6-turn budget. `gemma4:e4b-it-qat`'s turn-over-turn convergence versus
  `qwen3.5:9b-mlx`'s stuck loop is suggestive, not conclusive, on one run.

## Ranked follow-up

1. Test a discovery-mandatory condition: require at least one `reference
   authoring` call before a `scaffold` submission is even accepted by the
   harness, mirroring the prior (deleted) diagnostic's C0-vs-C1 comparison,
   to isolate whether that closes the gap.
2. Re-run `gemma4:e4b-it-qat` with a larger turn budget (it was still
   improving at turn 6) before concluding anything about compact-capabilities
   sufficiency for that model.
3. Consider a minimal worked `model.dm.json` example directly in the compact
   index's `_meta.usage` block or system-prompt-adjacent guidance — every
   model guessed plausible-looking but wrong top-level keys (`product`,
   `generate`, `demographics`), suggesting a one-shot example would remove
   most of the early-turn churn cheaper than more discovery calls would.
4. Investigate `qwen3.5:9b-mlx`'s identical-payload stuck loop specifically
   (turns 3–6) before drawing any comparison between it and the two Gemma
   variants — this looks like a distinct failure mode (ignoring feedback),
   not the same "wrong schema guess" failure the other two showed.
5. Re-run with seeds 42–46 across both a guided and unguided condition before
   making any GO/NO-GO claim about the compact index's real-world
   sufficiency — this diagnostic is one seed, three models, one condition.

## Verification commands

```bash
.venv/bin/pytest -q tests_ce/unit_tests/test_authoring/test_reference.py \
  tests_ce/unit_tests/test_docs/test_agent_cli_documentation_contract.py \
  tests_ce/functional_tests/test_cli/test_agent_cli_transport.py \
  tests_ce/functional_tests/test_cli/test_cli.py
.venv/bin/ruff check datamimic_ce
```

The gold-spec self-check (`scaffold --smoke-export --deterministic-replay` on
the hand-built T1 answer) is reproducible with the task definition above; it
is not committed as a fixture per this archive's evidence-outside-the-repo
convention.
