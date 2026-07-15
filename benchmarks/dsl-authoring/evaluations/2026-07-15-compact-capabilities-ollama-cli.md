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

Two conditions were run against the same task, oracle, seed, and turn budget:

- **Condition A — hand-rolled text protocol:** the model requests CLI
  invocations via a documented `CLI: <args>` text convention and submits its
  answer as a fenced ```json``` block. This mirrors what an agent with no
  native tool-calling support has to do.
- **Condition B — native Ollama tool-calling:** the same CLI commands exposed
  as OpenAI-style function-call tools (`datamimic_capabilities`,
  `datamimic_reference_authoring`, `datamimic_reference_scaffold`,
  `datamimic_scaffold_submit`), with `think: true` enabled. Added after
  Condition A's results raised the question of whether the failures were a
  capabilities-index sufficiency finding or a tool-use-protocol artifact —
  `ollama show <model>` confirmed all three models declare native `tools` and
  `thinking` capability, so Condition A was not exercising what these models
  are actually built for.

Context-window size was checked and ruled out as a factor for both
conditions: `ollama ps` reports the full native context allocated for each
model (`qwen3.5:9b-mlx` 262144 tokens, both `gemma4` variants 131072 tokens)
from the very first turn, and no Modelfile or request in either condition set
a smaller `num_ctx`. The conversations here (a handful of turns, each a few
KB) never came close to those limits.

## Contract and method

Isolation was enforced structurally in both conditions, not just by prompt:
the harness (`ollama_cli_eval.py` / `ollama_cli_eval_v2.py`, throwaway, not
committed) never imports `datamimic_ce`. Every DATAMIMIC interaction is a
`subprocess` call to the installed `.venv/bin/datamimic` console script,
restricted to an allow-list of subcommands (`--help`, `capabilities`,
`reference`, `scaffold`, `lint`, `dry-run`). The model's only knowledge of
DATAMIMIC is what those commands return in-conversation; it has no access to
repository source, tests, or documentation.

Budget: 6 turns total per model, seed 42, temperature 0.2, in both
conditions.

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

| Model | Local | Access (A) | Access (B) |
|---|---|---|---|
| `qwen3.5:9b-mlx` | yes (MLX) | pass | pass |
| `gemma4:e4b` | yes | pass | pass |
| `gemma4:e4b-it-qat` | yes | pass | pass |

All three models were reachable via the local Ollama server in both
conditions; no access failures. `-cloud`-tagged Ollama models were excluded —
they proxy to Ollama's cloud, not local inference, and were out of scope for
this "local model" test.

## Condition A — hand-rolled text protocol

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
  was visibly converging turn over turn.

Total wall-clock spent inside `scaffold` calls per model was small (2.9–3.7 s
across 5–6 calls each) — the bottleneck was authoring correctness, not CLI or
model latency.

## Condition B — native Ollama tool-calling

Same task/oracle/seed/budget; `datamimic_capabilities`,
`datamimic_reference_authoring`, `datamimic_reference_scaffold`, and
`datamimic_scaffold_submit` exposed as real function-call tools, `think:
true`. A pre-flight two-turn dry run against `gemma4:e4b` confirmed the
round-trip works before committing to the full run: turn 1 called
`datamimic_reference_scaffold`, turn 2 called `datamimic_scaffold_submit` —
already qualitatively different from Condition A's zero-discovery pattern for
the same model.

| Model | Discovery tool calls | `scaffold_submit` calls | No-tool-call turns | Turn reached `verified=true` | Outcome |
|---|---|---|---|---|---|
| `qwen3.5:9b-mlx` | 6 (`capabilities`, 5× `reference_authoring`) | 0 | 0 | — | fail: turn budget exhausted (never submitted) |
| `gemma4:e4b` | 3 (`reference_scaffold`, 2× `reference_authoring`) | 2 | 1 | — | fail: turn budget exhausted |
| `gemma4:e4b-it-qat` | 1 (`reference_scaffold`) | 4 | 1 | — | fail: turn budget exhausted |

**Still 0/3 verified within the same 6-turn budget — but the failure mode
changed substantially, in the direction the tool-calling hypothesis
predicted:**

- **`qwen3.5:9b-mlx`** now discovers instead of guessing: `capabilities` →
  `reference authoring` (full listing) → `reference authoring
  --category product --kind generated` → `--category field --kind int_range`
  → `--category field --kind values` → `--category entity --kind generated`
  (this last query names a category, `entity`, that does not exist in the
  taxonomy — a real query mistake, not a hallucinated tool). It used the
  entire budget on discovery and never attempted a submission, so the earlier
  "stuck loop repeating identical wrong output" failure mode is gone, replaced
  by "never stops discovering." Its visible `thinking` traces show genuine,
  reasonable step-by-step planning at every turn — a stark contrast to
  Condition A, where nothing about its reasoning was ever observable.
- **`gemma4:e4b`** went straight for the full JSON Schema (`reference
  scaffold`) on turn 1 rather than the compact index, then attempted a
  submission on turn 2 using an invented flat top-level shape (`fields`
  instead of nested `products[].fields`). After two `reference authoring`
  lookups (`field/identifier`, `field/increment`) and one turn that produced
  no tool call at all (a wasted turn — the model's `thinking` shows it was
  still reasoning about structure without emitting a call), its final
  submission at turn 6 used `"kind"` values from the *field* vocabulary
  (`increment`, `allowed_values`, `decimal_range`) at the *product* level,
  where only `generated`/`source`/`time_series` are valid — the same
  product-vs-field discriminator confusion seen in Condition A, just reached
  by a different path.
- **`gemma4:e4b-it-qat`** fetched the full schema once (turn 1), skipped a
  turn (turn 2, no tool call), then submitted four times in a row (turns
  3–6), each attempt restructuring the document (flat `fields` → nested
  `products[].fields` with per-field `"kind"` → per-field `roles[].kind` →
  a mix of the last two) without ever adding the required `"kind":
  "generated"` discriminator on the *product* object itself. Every one of the
  four submissions failed for a variant of the same root cause.

The recurring cross-model failure in Condition B is narrower and more
specific than Condition A's "wrong shape entirely": **all three models
correctly discovered they need a `products` array with `expectations`, and
correctly reused field-level "kind" vocabulary from `reference authoring`
lookups, but repeatedly missed or misapplied the separate product-level
`"kind"` discriminator** (`generated`/`source`/`time_series`), which
distinguishes the different product types. `datamimic_reference_authoring`
under `category=product, kind=generated` — the exact fragment that documents
this — was fetched by only one model (`qwen3.5:9b-mlx`, turn 3), and even
then it ran out of budget before submitting.

## Comparison

| | Condition A (text protocol) | Condition B (native tools) |
|---|---|---|
| Verified | 0/3 | 0/3 |
| Discovery calls used | 0–1 per model | 1–6 per model |
| Reasoning visible to evaluator | no | yes (`thinking`) |
| Dominant failure mode | guess blindly from invented syntax; one model stuck repeating an identical wrong payload | explore genuinely, converge on most of the structure, miss the product-level `kind` discriminator; one model never stops exploring |

Native tool-calling did not flip the pass/fail outcome inside the same
6-turn budget, but it changed *what* failed. Every model in Condition B
engaged with the actual discovery tools and made visible, generally sensible
progress; none exhibited Condition A's degenerate repeated-identical-output
loop. The remaining blocker narrowed from "wrong syntax across the board" to
one specific, nameable confusion (product-kind vs. field-kind) plus a turn
budget that was too tight for the models that spent it on thorough discovery
(`qwen3.5:9b-mlx`) or on slow iterative repair (`gemma4:e4b-it-qat`, visibly
still improving at turn 6).

## Decision

- **NO-GO (both conditions):** unattended CLI-only authoring by small local
  models within a 6-turn budget on this task. 0/3 verified in both
  conditions.
- **GO (tooling choice):** native tool-calling over a hand-rolled text
  protocol for any future local-model harness. It did not change the
  pass/fail count here, but it eliminated a degenerate failure mode (the
  identical-payload stuck loop), produced auditable reasoning traces, and
  measurably increased genuine discovery-tool usage — strictly better
  evidence quality for the same budget, independent of whether it changes the
  verified rate on a larger run.
- **NO DATA:** whether the compact `capabilities` index itself is a
  bottleneck. In Condition B, two of three models skipped `capabilities`
  entirely in favor of `reference scaffold` (the full JSON Schema) when both
  were offered as equally-weighted tools — suggesting the compact index's
  role is a token-budget optimization for cases where an agent doesn't need
  full detail, not a hard blocker when an agent does reach for the detailed
  path. No model in either condition was ever observed failing *because* the
  compact index specifically omitted something it needed and had no drill-down
  for.
- **NO DATA:** model ranking or reliability claims from a single seed and a
  6-turn budget, in either condition.

## Ranked follow-up

1. Re-run Condition B with a larger turn budget (10–12): `qwen3.5:9b-mlx` used
   its entire budget on discovery without ever submitting, and
   `gemma4:e4b-it-qat` was still iterating at turn 6 — both may simply need
   more room, not a different protocol.
2. Make the product-level `"kind"` discriminator harder to miss: either
   surface a one-line worked example (`{"kind": "generated", ...}` at the
   product level) directly in `capabilities`' compact index or in
   `reference scaffold`'s output, or strengthen the `invalid_discriminator`
   diagnostic to name the *product* vocabulary explicitly instead of relying
   on the model to infer it's a different `"kind"` than the field-level one
   it just saw. This is the single most common root cause across both
   conditions and all three models.
3. Test a discovery-budget guard: cap discovery calls (e.g. at 3) and require
   a submission attempt after that, so models like `qwen3.5:9b-mlx` that
   discover thoroughly but never converge to a submission are forced to test
   their understanding within the turn budget.
4. Re-run with seeds 42–46 across both conditions before making any GO/NO-GO
   claim about the compact index's real-world sufficiency or about
   native-tool-calling's effect on the verified rate — this diagnostic is one
   seed, three models, two conditions.
5. If a future harness is built for real (per this directory's "Contract for
   a future canonical harness"), it should default to native tool-calling per
   this diagnostic's Condition B evidence, and should log `thinking` traces
   in its hashed call ledger — they were the single most useful signal for
   understanding *why* a run failed, not just that it did.

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
convention. `ollama show <model>` (no arguments needed beyond the model tag)
reproduces the capability/context-length checks cited above.
