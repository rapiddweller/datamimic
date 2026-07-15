# A Five-Rung Difficulty Ladder for CLI-Only Agent Authoring of DATAMIMIC Intent Models — 2026-07-15

Single-seed study on `feat/capabilities-compact-index` (PR #215). Curated
record; raw transcripts, provider request identifiers, and runtime outputs
are intentionally not committed. Every number in this document is backed by
a machine-written ledger entry in the (uncommitted, scratchpad-local) run
records; nothing is reported from memory.

## Abstract

We test whether five locally-hosted open-weight models (3.8B–30B class,
Apple M5 Pro / 48GB) and one capable baseline (Claude Haiku) can author
verified DATAMIMIC `model.dm.json` documents across five data-generation
tasks of increasing structural difficulty, using only the `datamimic` CLI as
their knowledge source, under an identical guided prompt (worked example +
submit-early-repair strategy, previously shown to flip 0/9 → 5/5 on the
easiest task). Result: a clean capability gradient. Small generalist chat
models (Gemma-4 8B variants, Qwen3.5 9B) pass only the flat-record rung
(1/5). An agentic-tuned 8B (Ministral-3) adds the mixed-field rung (2/5). A
coding-specialized 30B MoE (Qwen3-Coder) adds the memstore-pipeline rung
(3/5) — the one rung the Haiku baseline itself failed. Haiku passes 4/5.
No participant passed all five rungs unaided. Two distinct failure classes
dominate: schema-shape errors (recoverable via the engine's structured
diagnostics) and intent-comprehension errors (invisible to the engine's
`verified` flag, caught only by an independent typed oracle). The relational
rung (T2) — nested children, per-parent counts, cross-product foreign keys —
is the sharpest small-model discriminator: zero local passes, and even the
baseline needed 7 of its 8 budgeted attempts.

## 1. Background

A prior diagnostic (`2026-07-15-compact-capabilities-ollama-cli.md`, same
directory) established on a single flat task (T1) that: (a) the DATAMIMIC
schema/CLI is learnable zero-shot by a capable model; (b) small local models
fail under a discover-first workflow but all pass under a guided prompt
(worked example + two schema-trap rules + submit-early-repair strategy); (c)
neither sampling configuration nor tool-calling protocol explains the
capability gap. This study extends that single task to a five-rung
difficulty ladder to locate *where* the guided workflow stops carrying small
models, with Haiku as the capability baseline.

## 2. Method

**Harness.** Identical to the prior study's Condition D harness, extended
for task parameterization: native Ollama tool-calling with four tools
(`datamimic_capabilities`, `datamimic_reference_authoring`,
`datamimic_reference_scaffold`, `datamimic_scaffold_submit`), each tool a
`subprocess` call to the installed `.venv/bin/datamimic` — the harness never
imports `datamimic_ce`, enforcing CLI-only isolation structurally. `think:
true` is requested only for models whose `api/show` capabilities declare
`thinking`. Sampling: only `seed: 42` is forced; all other sampling
parameters use each model's declared defaults. `num_ctx` is capped at 32768
after Ministral-3's native 262k default allocated a ~42GB KV cache on the
48GB machine, spilled to CPU, and produced mid-conversation HTTP 500s; no
conversation in this study approaches even a third of the 32k cap, and the
affected runs were cleared and re-run rather than patched around.

**Budget.** 8 turns per (model, task) cell — two more than the prior
study's 6, granted uniformly because the upper rungs are genuinely larger
documents. One turn = one model response; a response may carry multiple
batched tool calls.

**Guided prompt.** Constant across all tasks and models: the same
3-city worked example (shape only, never task content), the same two
schema-trap rules (top-level key whitelist; product-kind vs. field-kind
vocabulary), the same submit-early instruction (first submission by turn 2,
at most one discovery call before it, never resubmit unchanged).

**Gold-spec gate.** Every task's reference solution was authored by the
evaluator and verified against `datamimic scaffold --format json
--deterministic-replay` (reaching `ok: true, verified: true`) *before* any
model saw the task. Every task's typed oracle was then self-tested: it must
pass on the gold spec's scaffold output. All five oracles passed this gate.

**Typed oracle.** Per task, an independent check over `scaffold`'s raw
sample rows and product counts (uniqueness, domains, ranges, counts,
FK-sample validity), plus the engine's own `verified` flag. The oracle
result — including which specific checks failed — is fed back to the model
inside the tool response, so a model can repair intent-level misses, not
just schema-level ones. Verification requires **all** oracle checks to
pass; the engine flag alone is insufficient (see §6.3).

**Baseline protocol (Haiku).** One context-free Claude Haiku subagent per
task, forbidden from reading any repository file, restricted by prompt to
the same four CLI invocation forms, same guided-prompt text, same task
prompts, and an instructed budget of 8 total CLI invocations. Two protocol
differences from the local harness are unavoidable and disclosed: transport
(Claude agent with a Bash tool vs. Ollama chat API with function-calling),
and enforcement (the locals' budget is enforced by the harness; the
baseline's budget is instructed, and was in fact exceeded in one cell — see
§5). The baseline also initially lacked in-loop oracle feedback; where that
mattered (T5), the oracle result was delivered as a follow-up message and
the repair round is reported explicitly.

## 3. The task ladder

All tasks use seed 42. Difficulty is structural, not numerical: each rung
introduces a DSL concept absent from all rungs below it.

| Rung | Name | New concepts introduced | Gold-spec acceptance checks |
|---|---|---|---|
| T1 | Flat records | one product, three field kinds (increment/values/int_range) | 4 |
| T2 | Relational parent–child | nested `children` products, per-parent counts, FK via `script: parent.id` + `foreign_key` role, cross-product expectations | 7 |
| T3 | Mixed field kinds | `weighted` (values+weights), regex `pattern`, `constant`, decimals | 5 |
| T4 | Memstore pipeline | `targets: memstore`, second product `kind: source` reading back, `identifier`/`foreign_key` roles required by the engine's memstore-completeness gate | 9 |
| T5 | Time series | product `kind: time_series`, ISO-8601 window/interval, `series_count`, implied (not stated) row count 12 | 3 explicit + row-count via oracle |

Task prompts state business intent only — no schema hints beyond the
constant guided prompt. Full prompts are in the harness script; gold specs
reached `verified: true` with deterministic replay for every rung.

Notable gold-spec construction findings (the evaluator hit these before any
model did, confirming they are real schema hurdles, not model
hallucinations): T2's child FK must be `{"kind": "script", "script":
"parent.id"}` — a randomly generated FK field passes schema validation but
fails the per-parent-count acceptance check; the engine's own `fix_hint` on
the first wrong attempt names the `parent.` prefix. T4's
memstore-completeness gate requires exactly one consumer FK role targeting a
typed producer identifier — `ok: true` with 7/7 explicit checks still yields
`verified: false` until both roles are declared.

## 4. Participants

| Participant | Class | Size | Runs on |
|---|---|---|---|
| `gemma4:e4b` | generalist chat | ~8B | local (M5 Pro, 48GB) |
| `gemma4:e4b-it-qat` | generalist chat, QAT | ~8B | local |
| `qwen3.5:9b-mlx` | generalist chat | 9.4B | local (MLX) |
| `ministral-3:8b-instruct-2512-q4_K_M` | agentic-tuned instruct | 8B | local |
| `qwen3-coder:30b-a3b-q4_K_M` | coding/agentic MoE | 30B total / ~3B active | local |
| Claude Haiku | capable baseline | — | API (subagent) |

`phi4-mini:3.8b` was excluded: the prior study established it never emits
structured tool calls despite declaring `tools` capability, making every
cell an automatic no-contest.

## 5. Results

✓tN = oracle-verified at turn N (locals) / attempt N (baseline). ✗ = failed
within budget.

| Participant | T1 | T2 | T3 | T4 | T5 | Total |
|---|---|---|---|---|---|---|
| `gemma4:e4b` | ✓t2 | ✗ | ✗ | ✗ | ✗ | 1/5 |
| `gemma4:e4b-it-qat` | ✓t3 | ✗ | ✗ | ✗ | ✗ | 1/5 |
| `qwen3.5:9b-mlx` | ✓t4 | ✗ | ✗ | ✗ | ✗ | 1/5 |
| `ministral-3:8b` | ✓t5 | ✗ | ✓t4 | ✗ | ✗ | 2/5 |
| `qwen3-coder:30b-a3b` | ✓t2 | ✗ | ✓t2 | ✓t7 | ✗ | 3/5 |
| Claude Haiku (baseline) | ✓a1 | ✓a7 | ✓a2 | ✗ | ✓a3* | 4/5 |

\* T5 baseline: first submission was engine-verified but oracle-failed (see
§6.3); verified on overall attempt 3 after the oracle result was delivered.

Baseline protocol deviations, disclosed: on T2 the baseline used exactly its
8-invocation budget (verified on the 7th scaffold attempt). On T4 it
**exceeded** the instructed budget (~20 datamimic invocations per its own
report) and still ended at `verified: false` — under strict budget
enforcement its T4 cell would fail identically, so the 4/5 total is
unaffected, but per-attempt numbers for T4 are not budget-comparable.

## 6. Analysis

### 6.1 A clean capability gradient

Total scores order exactly by model class, not raw parameter count:
generalist 8–9B chat models (1/5, all three identical) < agentic-tuned 8B
(2/5) < coding-specialized 30B MoE (3/5) < capable baseline (4/5). Ministral
outscoring same-size Gemma/Qwen generalists, and Qwen3-Coder outscoring it
in turn, is consistent with tool-use/agentic fine-tuning mattering more than
scale at the small end. The single most striking cell: **`qwen3-coder`
passed T4 (memstore pipeline, turn 7) — the one rung the baseline failed.**
One cell on one seed is an anecdote, not a ranking; but it demonstrates the
ladder's upper rungs are within local-model reach, and that T4's difficulty
is of a different *kind* (role-declaration knowledge) rather than a pure
capability ceiling.

### 6.2 T2 (relational) is the sharpest discriminator

Zero local passes, and the baseline needed 7 of 8 attempts. The failure
chain is consistent across every participant that engaged: `min`/`max`
naming → nested-children shape → FK-as-random-value (schema-valid,
acceptance-invalid) → `parent.id` script syntax → roles-as-objects. Each
step is individually recoverable from the engine's diagnostics — the
baseline recovered through all five within budget; `qwen3-coder` got to the
last step (its final T2 submission failed only the FK-sample and
engine-verified oracle checks) and ran out of turns. The smaller models
never got past the first two steps, and the Gemma variants wasted 3–6 turns
per task emitting no tool call at all (a stall mode that reappears under
pressure even though the guided prompt eliminated it on T1).

### 6.3 Engine-verified is not intent-verified — two clean specimens

The study's most consequential finding for tooling design, observed
independently at both ends of the capability spectrum:

- **Baseline, T5:** first submission omitted `series_count: 2` (the "2
  parallel series" requirement), produced 6 rows instead of 12, and was
  `verified: true` — because the engine verifies only *declared*
  expectations. The typed oracle caught it; given the oracle result, the
  baseline repaired in one more scaffold attempt and — notably — articulated
  the lesson itself: "`verified: true` only certifies the expectations you
  declared; it is not a check against the business intent."
- **`qwen3-coder`, T5:** submitted `values: ["sensor1", "sensor2"]` for the
  sensor field — apparently misreading "2 parallel series" as two sensor
  *names* — and its final submission was schema-valid and engine-verified
  with only the oracle's `sensor_domain` check failing. Unlike the baseline,
  it never acted on that oracle feedback across five submissions: an
  intent-comprehension failure that no amount of schema diagnostics can fix.

Any production acceptance gate for agent-authored models therefore needs
intent-derived checks (or a reviewer) on top of `verified: true`; the flag
alone systematically passes documents that miss undeclared requirements.

### 6.4 Failure taxonomy across all 19 failed cells

1. **Schema-shape errors** (dominant in 8–9B generalists): `min`/`max` vs
   `minimum`/`maximum`, product/field/expectation `kind` discriminator
   confusion, invented attributes (`unique: true` on fields), wrong
   expectation field spellings. Recoverable in principle — these models
   recover on T1 but the error *volume* on larger documents exceeds an
   8-turn budget.
2. **Stalls** (Gemma variants only): 3–6 no-tool-call turns per failed task,
   the model reasoning in prose without emitting a call. The single largest
   budget drain for that family.
3. **Concept gaps** (mid-tier): Ministral's T4 failures center on the source
   product's shape (`source/id` missing, spurious `count`); its T2 failures
   on the relationship encoding. These are one-concept misses, not volume
   problems.
4. **Intent misses** (top-tier): §6.3 — schema-perfect, intent-wrong.
   Uniquely dangerous because every engine signal reads green.
5. **Infrastructure noise** (excluded from scores, documented): Ministral's
   native 262k context allocation caused OOM-driven HTTP 500s on the 48GB
   host; cells affected were cleared and re-run with `num_ctx: 32768`. One
   T3 pass survived from the affected batch (it completed before the
   pressure built) and was retained; its replay-determinism makes
   contamination implausible.

### 6.5 The one-worked-example ceiling

The guided prompt's worked example shows a flat single-product document.
Its transfer tracks structural distance: T1 (same shape) — 6/6 participants
pass; T3 (same shape, new field kinds) — 3/6; T2/T4/T5 (new *structural*
concepts: nesting, pipelines, time windows) — 0/5 locals, baseline 2/3.
The earlier study's "productize the worked example" recommendation
therefore under-specifies: one example per *structural family* (flat,
nested-relational, pipeline, time-series) is the indicated shape, not one
example globally.

## 7. Threats to validity

- **Single seed, single run per cell.** No reliability claim; the gradient's
  cleanness (three identical 1/5 rows; strict ordering by class) is
  suggestive but unreplicated. Seeds 42–46 remain future work.
- **Baseline transport differs** (§2), and its T4 budget overrun means T4
  attempt-counts are not comparable across participants (pass/fail is).
- **Oracle-feedback asymmetry on T5**: locals had the oracle in-loop from
  turn 1; the baseline received it post-hoc. The reported a3* makes the
  asymmetry explicit rather than hiding it; under an in-loop oracle the
  baseline would plausibly have repaired one attempt sooner.
- **Guided prompt was tuned on T1 failures** (prior study). T1 results are
  therefore partially circular for the locals; T2–T5 results are not (the
  prompt contains nothing about children, memstore, roles, or windows).
- **The evaluator authored both gold specs and oracles.** The gold-gate
  protocol (spec must verify, oracle must pass on gold, before any model
  runs) bounds but does not eliminate design bias — e.g., T5's implied row
  count is only as fair as the phrase "2 parallel series" is unambiguous,
  and one local model demonstrably parsed it differently.
- **Ollama-hosted quantized weights** (Q4_K_M) may understate the FP16
  capability of every local model tested.

## 8. Conclusions and future work

Under a guided prompt that fully solves the flat-record case, structural
document complexity — not field-kind variety — is what separates small local
models from a capable baseline on CLI-only DATAMIMIC authoring. The
practical rungs for local deployment today: 8–9B generalists are reliable
only for flat single-product models; an agentic-tuned 8B adds rich flat
models; a coding-tuned 30B MoE reaches pipelines but not relational
hierarchies within tight budgets. The engine's `verified` flag must not be
the sole acceptance gate for any of them — nor for the baseline.

Priority follow-ups: (1) per-structural-family worked examples in the
agent-facing guidance, re-run the ladder; (2) seeds 42–46 replication; (3)
budget-extension study for the near-miss cells (`qwen3-coder` T2 was one
concept from passing); (4) an in-loop intent oracle as a first-class
`scaffold` feature — both §6.3 specimens would have been caught at authoring
time by machine-checkable derived expectations (e.g., "N parallel series"
implies a derivable row count the engine already knows from the compile
plan).

## Reproduction

Harness: `ollama_cli_eval_v4_ladder.py` (scratchpad, uncommitted per this
archive's convention); gold specs under `gold_specs/` alongside it. Gold
gate: `datamimic scaffold <gold> --format json --deterministic-replay` must
report `verified: true` for every task before any model run. Oracle
self-test: every oracle must pass on its gold output. Local runs:
`python3 ollama_cli_eval_v4_ladder.py "<model>" "T1,T2,T3,T4,T5"` with
results accumulating incrementally (crash-safe, resumable). Verification
commands for the repository state this study ran against:

```bash
.venv/bin/pytest -q tests_ce/unit_tests/test_authoring tests_ce/unit_tests/test_docs \
  tests_ce/functional_tests/test_cli
.venv/bin/ruff check datamimic_ce
```
