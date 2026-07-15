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

Three conditions were run, added incrementally as each answer raised the next
question (plus a corrected-sampling rerun of Condition B, "B2" — see its own
section — after a review question surfaced that Condition B's sampling
config was not best-practice):

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
- **Condition C — Claude Haiku, cleanroom, no harness:** after Condition B
  still found 0/3 verified, the open question became whether the DATAMIMIC
  schema/CLI itself was the obstacle, independent of model scale. A single
  context-free Claude Haiku subagent (no memory of this conversation,
  forbidden from reading any repository file) was given the same business
  intent and only the raw `datamimic` binary via an unrestricted Bash tool —
  not the fixed 4-function harness used in B. This is **not** a controlled
  replication of A/B (different tooling, different budget shape — see the
  condition's own section for the exact caveat); it answers a narrower
  question: can *any* competent model solve this at all, zero-shot,
  cleanroom.

Context-window size was checked and ruled out as a factor for Conditions A/B:
`ollama ps` reports the full native context allocated for each
model (`qwen3.5:9b-mlx` 262144 tokens, both `gemma4` variants 131072 tokens)
from the very first turn, and no Modelfile or request in either condition set
a smaller `num_ctx`. The conversations here (a handful of turns, each a few
KB) never came close to those limits.

## Contract and method

Isolation was enforced structurally in Conditions A and B, not just by
prompt: the harness (`ollama_cli_eval.py` / `ollama_cli_eval_v2.py`,
throwaway, not committed) never imports `datamimic_ce`. Every DATAMIMIC
interaction is a `subprocess` call to the installed `.venv/bin/datamimic`
console script, restricted to an allow-list of subcommands (`--help`,
`capabilities`, `reference`, `scaffold`, `lint`, `dry-run`). The model's only
knowledge of DATAMIMIC is what those commands return in-conversation; it has
no access to repository source, tests, or documentation. Condition C's
isolation is prompt-level only (a documented instruction to the agent, not a
subprocess allow-list) — see that condition's own section.

Budget: 6 turns total per model, seed 42, temperature 0.2, in Conditions A
and B. Condition C's budget is shaped differently — see its section.

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
| `gemma4:31b-cloud` | no (Ollama cloud) | not run | pass |
| `nemotron-3-nano:30b-cloud` | no (Ollama cloud) | not run | pass |
| `gpt-oss:120b-cloud` | no (Ollama cloud) | not run | pass |
| `qwen3.5:cloud` | no (Ollama cloud) | not run | **fail — subscription required** |
| `mistral-large-3:675b-cloud` | no (Ollama cloud) | not run | **fail — subscription required** |
| `deepseek-v4-flash:cloud` | no (Ollama cloud) | not run | **fail — subscription required** |

Three of the requested cloud models returned `HTTP 403` / "this model
requires a subscription, upgrade for access" on every chat request — a
real access gate, not a harness bug (`api/show` on these models succeeds and
reports normal capabilities; only the actual inference call is gated). This
matches a prior, now-deleted diagnostic's finding that `qwen3.5:cloud`
specifically was inaccessible. These three are excluded from all semantic
denominators below, per this archive's own access/semantic separation
convention.

The three genuinely local models were reachable via the local Ollama server
in both conditions; no access failures. `-cloud`-tagged Ollama models were
excluded from the original scope — they proxy to Ollama's cloud, not local
inference — but `gemma4:31b-cloud` was added to Condition B on request, as a larger
(31B vs. 8-9B) reference point run through the identical harness/budget.

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
| `gemma4:31b-cloud` | 6 (`capabilities`, `reference_scaffold`, 4× `reference_authoring`) | 0 | 0 | — | fail: turn budget exhausted (never submitted) |

**Still 0/4 verified within the same 6-turn budget — but the failure mode
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
- **`gemma4:31b-cloud`** (31B, ~3.5–7x larger than the local models) was, if
  anything, *more* thorough than the smaller models, not less: `capabilities`
  → `reference scaffold` (full schema) → `reference authoring
  --category field` (a broad, kind-less listing call) → `--category product
  --kind generated` → `--category field --kind increment` → `--category
  field --kind int_range`. It never attempted a single submission — the
  entire 6-turn budget went to careful, well-targeted discovery, including
  the one query (`product`/`generated`) that documents the exact
  discriminator every other model in this diagnostic got wrong. Whether it
  would have gotten the discriminator right had it had one more turn to
  submit is unanswered; this run cannot distinguish "would have failed the
  same way" from "would have passed" because it never reached the submission
  step.
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
this — was fetched by only two models in Condition B (`qwen3.5:9b-mlx` turn
3, `gemma4:31b-cloud` turn 4), and neither of those two ever submitted, so
neither had the chance to demonstrate they'd actually internalized it.

## Condition C — Claude Haiku, cleanroom, no harness

A single context-free Claude Haiku subagent (spawned fresh, no memory of this
conversation or this report's findings) was given the T1 business intent and
told its only source of DATAMIMIC knowledge was the raw `datamimic --help`/
`capabilities`/`reference`/`scaffold` CLI, invoked via an unrestricted Bash
tool. It was explicitly forbidden from reading any file in the repository.
Budget was framed differently than A/B: "at most 10 scaffold attempts"
rather than a fixed count of total turns, and discovery calls were
effectively unlimited (ordinary Bash invocations, not a rationed tool-call
budget) — **this is a looser, more favorable budget shape than Condition B's
6-turn total**, so a direct pass-rate comparison to A/B would overstate the
capability gap. Treat this as answering "can a competent model solve this
zero-shot at all," not "would it also pass under B's exact constraints."

Commands run, in order:

```text
datamimic --help
datamimic capabilities
datamimic reference scaffold
datamimic scaffold <tmp-file> --format json --smoke-export --deterministic-replay
```

**Result: `verified: true` on the first and only scaffold attempt.** All 4
acceptance checks passed (`exact_count`, `unique`, `allowed_values`, `range`),
deterministic replay passed. The submitted document correctly used
`"kind": "generated"` at the product level and the right field-level kinds
(`increment`, `values`, `int_range`) on the first try — the exact
product-vs-field discriminator distinction that tripped up every model in
Conditions A and B. It also added explicit `expectations` for `unique`,
`allowed_values`, and `range` unprompted — closer to the hand-built gold
spec than any Condition A/B submission got. Self-reported confusion points:
none; the agent's own report states the schema was "clear and consistent
after exploring the reference documentation."

## Errata: Condition B's sampling was not best-practice, and B2 corrects it

**Condition B's four model runs above (`qwen3.5:9b-mlx`, `gemma4:e4b`,
`gemma4:e4b-it-qat`, `gemma4:31b-cloud`) forced `temperature: 0.2` on every
request.** That was inherited unreflected from a prior, now-deleted
harness's determinism-first design and never re-checked against these
specific models. `ollama show <model> --parameters` shows every locally
declared model in this diagnostic lists `temperature: 1` (not 0.2) as its own
default — `top_p 0.95`/`top_k 20-64` and, for `qwen3.5:9b-mlx`,
`presence_penalty 1.5`, are also part of each model's declared configuration.
Overriding only `temperature` deviates from the model's own tuned defaults
without a stated reason; this is not best practice.

**Condition B2** re-runs the same task/oracle/seed/6-turn budget/tool
schema, with the harness fixed to send only `seed` in `options` — every
other sampling parameter now falls back to each model's own declared
default. It also adds the newly-requested models
(`nemotron-3-nano:30b-cloud`, `gpt-oss:120b-cloud`, plus `qwen3.5:cloud` and
`mistral-large-3:675b-cloud`/`deepseek-v4-flash:cloud`, all three of which
turned out to be access-gated — see Access gate above).

| Model | Discovery tool calls | `scaffold_submit` calls | No-tool-call turns | Verified? |
|---|---|---|---|---|
| `qwen3.5:9b-mlx` | 6 | 0 | 0 | no — turn budget exhausted, never submitted |
| `gemma4:e4b` | 1 | 5 | 0 | no — turn budget exhausted |
| `gemma4:e4b-it-qat` | 4 | 1 | 1 | no — turn budget exhausted |
| `gemma4:31b-cloud` | 6 | 0 | 0 | no — turn budget exhausted, never submitted |
| `nemotron-3-nano:30b-cloud` | 6 | 0 | 0 | no — turn budget exhausted, never submitted |
| `gpt-oss:120b-cloud` | 6 | 0 | 0 | no — turn budget exhausted, never submitted |

**0/6 verified — correcting the sampling defaults did not change the
pass/fail outcome for any of the four re-run models, and neither new model
(`nemotron-3-nano:30b-cloud`, `gpt-oss:120b-cloud`) verified either.** It did
change qualitative behavior, in ways that cut against a simple "low
temperature caused the failures" story:

- **`gemma4:e4b`** is the clearest case: at `temperature: 0.2` (original
  Condition B) it made 2 distinct submission attempts with genuinely
  different, evolving mistakes. At `temperature: 1` (its own declared
  default, Condition B2) it made 5 submission attempts, but turns 3–6
  resubmitted the **exact same** invalid payload four times in a row
  (`invalid_discriminator` on the product `"kind"`, unchanged) — the same
  degenerate stuck-loop pattern seen in Condition A's `qwen3.5:9b-mlx` run,
  now reproduced in Condition B under correct sampling. Its first attempt
  (turn 2) also invented a completely different, more elaborate wrong shape
  (`components`/`data_source`/`field_definition` wrappers, `unique_integer`
  as a field kind) than anything seen at the lower temperature — consistent
  with higher temperature increasing the variety of wrong guesses without
  increasing correctness.
- **`qwen3.5:9b-mlx`** and **`gemma4:31b-cloud`** show the same
  "thorough-discovery, never submits" pattern as at `temperature: 0.2`,
  including `qwen3.5:9b-mlx` making an invalid query (`category: entity,
  kind: composite`) and redundantly re-fetching `capabilities` a second
  time at turn 5.
- **`nemotron-3-nano:30b-cloud`** (new) used its entire budget on discovery
  and never submitted, but its query targeting was visibly weaker than the
  other models': `category: entity, kind: record`, `category: product,
  kind: record`, and `category: field, kind: enum` are all invalid
  category/kind combinations (the correct kind for an enumerated set of
  values is `values`, not `enum`) — three of its six discovery calls queried
  fragments that do not exist.
- **`gpt-oss:120b-cloud`** (new) shows the most sophisticated visible
  reasoning of any model in this diagnostic — its `thinking` traces correctly
  name `ExactCountExpectation` and an `identifier` field role before it has
  even queried them — but it still used its entire budget on discovery and
  never submitted. Two of its six calls were pure waste: turn 3 queried an
  invalid fragment (`category: product, kind: definition`), and turn 5
  re-queried `category: product, kind: generated` — a fragment it had
  already fetched (correctly) at turn 4 — before spending its final turn
  re-fetching `reference scaffold` a second time (also already fetched, at
  turn 1) instead of attempting a submission. Sophisticated reasoning did not
  translate into efficient budget use here.

The corrected-sampling data does not support "Condition B's original 0/4 was
an artifact of bad temperature" — the outcome is unchanged, and the one
model whose behavior changed most (`gemma4:e4b`) got a new failure mode, not
a better one. The sampling fix was still the right thing to do (self-imposed,
uncorrected parameter deviation is not something to leave standing simply
because it happened not to flip the result here), and it is documented as an
erratum rather than silently overwriting the original Condition B numbers.
Across B2's six accessible models, four (`qwen3.5:9b-mlx`,
`gemma4:31b-cloud`, `nemotron-3-nano:30b-cloud`, `gpt-oss:120b-cloud`) never
attempted a single submission — discovery-budget exhaustion, not incorrect
submissions, is now the single most common outcome in this diagnostic.

## Comparison

| | Condition A (text protocol) | Condition B (native tools, temp=0.2) | Condition B2 (native tools, model-default sampling) | Condition C (Haiku, cleanroom) |
|---|---|---|---|---|
| Verified | 0/3 | 0/4 | 0/6 | 1/1 |
| Discovery calls used | 0–1 per model | 0–6 per model | 1–6 per model | 3 (unrationed) |
| Submission attempts before pass | — | — | — | 1 |
| Reasoning visible to evaluator | no | yes (`thinking`) | yes (`thinking`) | yes (agent's own report) |
| Dominant failure mode | guess blindly from invented syntax; one model stuck repeating an identical wrong payload | explore genuinely, converge on most of the structure, miss the product-level `kind` discriminator; two of four never even reach submission | same discriminator confusion; `gemma4:e4b` develops its own stuck loop (4 identical resubmissions); 4 of 6 models never submit at all, including the most articulate reasoner (`gpt-oss:120b-cloud`) | none observed |

Native tool-calling did not flip the pass/fail outcome inside the same
6-turn budget, but it changed *what* failed relative to Condition A. Every
model in B/B2 engaged with the actual discovery tools and made visible,
generally sensible progress; the one exception — `gemma4:e4b`'s stuck loop
in B2 — shows that the "identical repeated payload" pattern is not
specific to Condition A's text protocol or to low temperature; it recurred
under native tool-calling with correct sampling too, just in a different
model. The remaining blocker narrowed from "wrong syntax across the board"
to one specific, nameable confusion (product-kind vs. field-kind) plus, for
most B/B2 models, a turn budget spent substantially or entirely on discovery
with too little left for a converged submission.

Condition C's clean first-attempt pass is the most important single data
point in this diagnostic: it demonstrates the DATAMIMIC schema and CLI
surface, including the compact `capabilities` index, is not inherently
confusing or under-specified — a capable model resolved the exact
discriminator confusion that stumped every Condition A/B model, using less
discovery than several of them. That reframes Condition B's 0/4 as evidence
about small-model (8B–31B, open-weight, as currently prompted) capability and
budget, not evidence against the compact-index design PR #215 introduces.
The budget-shape difference from Condition B means this is directional, not
conclusive — see follow-up #1.

## Decision

- **NO-GO (Conditions A/B/B2):** unattended CLI-only authoring by small-to-
  large (8B–120B), open-weight/proprietary-weight local/Ollama-hosted models
  within a 6-turn budget on this task. 0/10 verified across all three
  conditions and nine distinct model runs (`gemma4:e4b`/
  `gemma4:e4b-it-qat`/`qwen3.5:9b-mlx`/`gemma4:31b-cloud` once each in both B
  and B2 plus `nemotron-3-nano:30b-cloud`/`gpt-oss:120b-cloud` in B2 only).
- **Confirmed: Condition B's original sampling was not best-practice**
  (forced `temperature: 0.2` against every model's own declared default of
  `1`), **but correcting it (B2) did not change the outcome.** 0/6 verified
  under model-default sampling, same as 0/4 under the forced low temperature.
  One model's *failure mode* changed (a new stuck loop in `gemma4:e4b`), not
  its pass/fail result. Sampling defaults are not the explanation for these
  models' failures.
- **GO (schema/CLI is not the blocker):** Condition C shows a competent model
  resolves the whole task, including the exact discriminator confusion every
  A/B/B2 model hit, zero-shot and cleanroom, with less discovery than several
  A/B/B2 models used. The compact `capabilities` index and the rest of the
  CLI surface are not implicated as the cause of the A/B/B2 failures.
- **GO (tooling choice):** native tool-calling over a hand-rolled text
  protocol for any future local-model harness. It did not change the
  pass/fail count in A vs. B/B2, but it produced auditable reasoning traces
  and measurably increased genuine discovery-tool usage — strictly better
  evidence quality for the same budget, independent of whether it changes the
  verified rate on a larger run. (It did not reliably eliminate the
  identical-payload stuck loop either — see B2's `gemma4:e4b`.)
- **Access, not capability, is the finding for three of the eight requested
  cloud models:** `qwen3.5:cloud`, `mistral-large-3:675b-cloud`, and
  `deepseek-v4-flash:cloud` all require an Ollama subscription this
  environment doesn't have. No semantic conclusion is possible for these
  three.
- **NO DATA:** whether the compact `capabilities` index itself is a
  bottleneck. Across B/B2, most models skipped `capabilities` entirely in
  favor of `reference scaffold` (the full JSON Schema) when both were
  offered as equally-weighted tools — suggesting the compact index's role is
  a token-budget optimization for cases where an agent doesn't need full
  detail, not a hard blocker when an agent does reach for the detailed path.
  No model in any condition was ever observed failing *because* the compact
  index specifically omitted something it needed and had no drill-down for.
- **NO DATA:** whether the models that spent their entire B2 budget on
  discovery without ever submitting (`qwen3.5:9b-mlx`, `gemma4:31b-cloud`,
  `nemotron-3-nano:30b-cloud`, `gpt-oss:120b-cloud` — four of six in B2,
  including a 120B model with the most articulate visible reasoning of any
  model tested) would pass under a Condition-C-shaped budget (more turns,
  unrationed discovery). Discovery-budget exhaustion, not incorrect
  submission, is now the single most common outcome in this diagnostic, and
  none of these four ever got to demonstrate whether their discovery had
  actually converged on a correct understanding.
- **NO DATA:** model ranking or reliability claims from a single seed, small
  model/condition counts, and (for Condition C) a single run.

## Ranked follow-up

1. Run Condition C's exact task/prompt through Condition B2's exact harness
   (fixed 4-tool schema, 6-turn budget, subprocess isolation, model-default
   sampling) with a capable model, to get one genuinely controlled A/B/C
   comparison — the current Condition C result is suggestive but was run
   with a different budget shape and tool surface, which this diagnostic has
   been explicit about not controlling for. This is the single highest-value
   remaining gap.
2. Re-run Condition B2 with a larger turn budget (10–12) for the four
   discovery-only models (`qwen3.5:9b-mlx`, `gemma4:31b-cloud`,
   `nemotron-3-nano:30b-cloud`, `gpt-oss:120b-cloud`) — this directly tests
   whether they "ran out of time" or "would have failed the same way as
   `gemma4:e4b`/`gemma4:e4b-it-qat`." Worth prioritizing `gpt-oss:120b-cloud`
   specifically: its reasoning was the most sophisticated observed, but two
   of its six calls were pure waste (one invalid query, one exact duplicate
   of an already-fetched fragment) — a stricter "don't repeat a fragment
   you've already fetched" instruction alone might be enough to free up the
   turn it needed to submit.
3. Make the product-level `"kind"` discriminator harder to miss: either
   surface a one-line worked example (`{"kind": "generated", ...}` at the
   product level) directly in `capabilities`' compact index or in
   `reference scaffold`'s output, or strengthen the `invalid_discriminator`
   diagnostic to name the *product* vocabulary explicitly instead of relying
   on the model to infer it's a different `"kind"` than the field-level one
   it just saw. This is the single most common root cause across every
   condition and every model that reached a submission.
4. Investigate `gemma4:e4b`'s stuck loop in B2 specifically (4 byte-identical
   resubmissions of a payload already known to fail) — this is the second
   time this exact degenerate pattern has appeared (Condition A's
   `qwen3.5:9b-mlx`, now B2's `gemma4:e4b`), in different models under
   different protocols and sampling settings, which suggests it may be a
   more general Ollama chat-loop artifact (e.g. the model's context making
   near-identical continuations likely) rather than a property of any one
   model or setting.
5. Test a discovery-budget guard: cap discovery calls (e.g. at 3) and require
   a submission attempt after that, so models that discover thoroughly but
   never converge to a submission are forced to test their understanding
   within the turn budget.
6. Re-run with seeds 42–46 across all conditions before making any GO/NO-GO
   claim about the compact index's real-world sufficiency or about
   native-tool-calling's/sampling's effect on the verified rate — this
   diagnostic is one seed throughout.
7. If a future harness is built for real (per this directory's "Contract for
   a future canonical harness"), it should default to native tool-calling and
   each model's own declared sampling defaults (never an arbitrary uniform
   temperature), and should log `thinking` traces (or, for Claude-family
   agents, the agent's own self-reported call sequence) in its hashed call
   ledger — they were the single most useful signal in this diagnostic for
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
