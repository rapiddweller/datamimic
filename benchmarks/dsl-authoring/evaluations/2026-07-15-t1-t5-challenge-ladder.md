# A Five-Rung Difficulty Ladder for CLI-Only Agent Authoring of DATAMIMIC Intent Models — 2026-07-15/16

Single-seed study on `feat/capabilities-compact-index` (PR #215). This is the
sole committed record of this evaluation series; it is self-contained. Every
number is backed by a machine-written ledger entry in the (scratchpad-local,
uncommitted) run records. Every prompt shown is verbatim.

## Abstract

Five locally-hosted open-weight models (3.8B–30B class, Apple M5 Pro / 48GB)
and one capable baseline (Claude Haiku) attempt to author verified DATAMIMIC
`model.dm.json` documents across five data-generation tasks of increasing
structural difficulty, using only the `datamimic` CLI as their knowledge
source, under an identical guided prompt. Result: a clean capability
gradient — generalist 8–9B chat models pass only the flat-record rung (1/5);
an agentic-tuned 8B adds the mixed-field rung (2/5); a coding-specialized
30B MoE scores 3/5 by the pre-registered oracle — but its memstore-pipeline
"pass" is reclassified on inspection as an **oracle loophole** (it generated
a look-alike duplicate instead of the required read-back pipeline), making
its intent-true score 2/5. The baseline passes 4/5. **On the true intent, no
participant passed the memstore-pipeline rung (T4)**, and the relational
rung (T2) had zero local passes with the baseline needing 7 of 8 attempts.
Three findings matter beyond the scores: (1) engine-verified ≠
intent-verified, demonstrated at both capability extremes; (2) a typed
oracle is itself an artifact that can be gamed unintentionally and needs the
same scrutiny as the systems it judges; (3) the memstore rung fails
participants not on capability but on one under-documented pairing of
field-level role declarations.

## 1. Background (self-contained)

Predecessor experiments on the same branch (superseded by this record)
established, on the flat task only: small local models fail 0/9 under a
"discover the schema before writing" prompt, independent of tool-calling
protocol and sampling configuration; the identical models pass 5/5 under a
guided prompt (worked example + two schema-trap rules + submit-early
strategy); a capable model solves the flat task zero-shot cleanroom either
way. Conclusion carried into this study: the guided workflow is the right
baseline condition, and the open question is where it stops carrying small
models as structural difficulty rises.

## 2. Scope — who ran, on what

| Participant | Class | Size | Quantization | Host |
|---|---|---|---|---|
| `gemma4:e4b` | generalist chat | ~8B | as shipped | local Ollama, M5 Pro 48GB |
| `gemma4:e4b-it-qat` | generalist chat, QAT | ~8B | QAT | local Ollama |
| `qwen3.5:9b-mlx` | generalist chat | 9.4B | nvfp4 (MLX) | local Ollama |
| `ministral-3:8b-instruct-2512-q4_K_M` | agentic-tuned instruct | 8B | Q4_K_M | local Ollama |
| `qwen3-coder:30b-a3b-q4_K_M` | coding/agentic MoE | 30B total / ~3B active | Q4_K_M | local Ollama |
| Claude Haiku | capable baseline | — | — | API subagent |

Excluded with reason: `phi4-mini:3.8b` (declares `tools` capability but
never emits structured tool calls — every cell would be an automatic
no-contest); Ollama `-cloud` models (not local; three additionally
subscription-gated, one retired by Ollama on test day).

## 3. Method

**Harness (local models).** Native Ollama tool-calling; four tools, each
one a `subprocess` call to the installed `.venv/bin/datamimic` (the harness
never imports `datamimic_ce` — CLI-only isolation is structural, not
prompt-level):

| Tool | Maps to |
|---|---|
| `datamimic_capabilities` | `datamimic capabilities` (compact index) |
| `datamimic_reference_authoring` | `datamimic reference authoring [--category C --kind K]` |
| `datamimic_reference_scaffold` | `datamimic reference scaffold` (full AuthoringSpecV1 JSON Schema) |
| `datamimic_scaffold_submit` | `datamimic scaffold - --format json --deterministic-replay` (stdin) |

Settings: seed 42 forced; all sampling parameters at each model's declared
defaults; `think: true` only for models declaring `thinking` capability;
`num_ctx: 32768` (capped after Ministral-3's native 262k default allocated a
~42GB KV cache on the 48GB host, spilled to CPU, and produced
mid-conversation HTTP 500s — affected cells were cleared and fully re-run,
not patched; no conversation in this study used more than a third of 32k).
Budget: 8 turns per (model, task) cell; one turn = one model response,
which may batch several tool calls. Submission errors and the typed-oracle
result (including which named checks failed) are fed back to the model in
the tool response, so both schema-level and intent-level misses are
repairable in-loop.

**System prompt — verbatim, constant across all tasks and models:**

```text
You are authoring a DATAMIMIC model.dm.json document.

Here is a minimal valid model.dm.json, for a DIFFERENT task (3 cities, one
text field), so you can see the exact document shape:

{
  "version": "1",
  "seed": 7,
  "products": [
    {
      "kind": "generated",
      "name": "cities",
      "count": 3,
      "fields": [
        {"kind": "values", "name": "region", "values": ["north", "south"]}
      ]
    }
  ]
}

Rules that matter: the top level allows ONLY version, seed, products,
expectations. Every product needs a "kind" (product-level kinds are
generated/source/time_series -- different vocabulary from field-level
kinds). Field-level kinds include increment, values, weighted, int_range,
decimal_range, pattern, constant, script, and others discoverable via
datamimic_reference_authoring.

Strategy: call datamimic_scaffold_submit with your best attempt EARLY -- by
your second turn at the latest. The submission errors are structured
(path/code/message/allowed_fields) and diagnostics carry a fix_hint; they
are the fastest way to learn the schema. Repair from them instead of doing
more discovery. Never resubmit an unchanged document. Use at most ONE
discovery call before your first submission.
```

**Baseline protocol (Haiku).** One context-free subagent per task,
forbidden from reading any repository file, restricted by prompt to the same
four CLI invocation forms, given the identical guidance text above plus the
identical task prompt, and an instructed budget of 8 total `datamimic`
invocations. Disclosed differences from the local harness: transport (Bash
tool vs. function-calling API); budget enforcement (instructed vs.
harness-enforced — violated once, see §6); oracle feedback initially absent
(delivered post-hoc where it mattered, T5, reported explicitly).

**Gold gate.** Before any model ran: an evaluator-authored gold spec per
task reached `ok: true, verified: true` with deterministic replay, and each
task's typed oracle was self-tested to pass on that gold output. 5/5 golds
and 5/5 oracle self-tests passed.

## 4. The tasks — verbatim prompts and oracles

All tasks use seed 42. Difficulty is structural: each rung introduces a DSL
concept absent from all rungs below it.

### T1 — flat records

```text
Business intent: produce a DATAMIMIC model.dm.json that generates
exactly 5 records for a product named "records". Each record has:
- id: a globally unique integer identifier
- category: exactly one of "A", "B", "C"
- score: an integer between 10 and 20 inclusive

Use seed 42.
```

Oracle: count==5; ids distinct integers; category ∈ {A,B,C}; score ∈
[10,20]; engine `verified` true.

### T2 — relational parent–child

```text
Business intent: produce a DATAMIMIC model.dm.json for a relational
parent-child dataset:
- product "customers": exactly 4 rows, each with a globally unique integer id
  and a region that is exactly one of "north", "south", "east", "west".
- each customer has EXACTLY 2 child rows in a product named "orders"; each
  order carries a customer_id that references its own parent customer's id,
  and an amount between 10.0 and 500.0.
- declare expectations for: the exact customer count, customer id uniqueness,
  exactly 2 orders per customer, the orders->customers foreign key, and the
  amount range.

Use seed 42.
```

Oracle: customers count==4 / orders count==8; customer ids unique; region
domain; every sampled order's customer_id ∈ sampled customer ids; sampled
amounts ∈ [10.0, 500.0]; engine `verified` true.

### T3 — mixed field kinds

```text
Business intent: produce a DATAMIMIC model.dm.json that generates
exactly 10 rows for a product named "tickets". Each ticket has:
- id: a globally unique integer identifier
- priority: weighted random value -- "low" with weight 0.6, "medium" with
  weight 0.3, "high" with weight 0.1
- code: a string matching the regular expression pattern TCK-[0-9]{4}
- handling_fee: a decimal between 0.5 and 9.99
- channel: always the constant string "web"

Declare expectations for the exact count, id uniqueness, the allowed
priority values, and the handling_fee range. Use seed 42.
```

Oracle: count==10; sampled ids unique; priority domain; code matches
`TCK-[0-9]{4}`; fee ∈ [0.5, 9.99]; channel=="web"; engine `verified` true.

### T4 — memstore pipeline

```text
Business intent: produce a DATAMIMIC model.dm.json for a two-stage
memstore pipeline:
- product "users": exactly 5 rows -- globally unique integer id, region
  exactly one of "eu", "us", "apac", credit_limit an integer between 100 and
  1000. Write this product into a memstore.
- product "user_audit": read the users back OUT of that memstore as a second
  product, exposing the same three fields (id, region, credit_limit). The
  audit ids must reference the user ids (foreign key).

Declare expectations for both products' exact counts, user id uniqueness,
the audit region domain, and the audit credit_limit range. Use seed 42.
```

Oracle (as pre-registered): users count==5; audit count==5; user ids
unique; audit region domain; audit credit ∈ [100,1000]; sampled audit ids ⊆
user ids; engine `verified` true. **Known gap, discovered post-hoc (§7.2):
no check asserts the audit product is actually `kind: source` reading from
the memstore** — a generated look-alike satisfies every listed check.

### T5 — time series

```text
Business intent: produce a DATAMIMIC model.dm.json for a time-series
product named "readings":
- 2 parallel series over the window 2026-01-01T00:00:00 to
  2026-01-01T06:00:00 with an interval of one hour (ISO-8601 duration PT1H)
- each row has: sensor, exactly one of "temp" or "humidity", and value, a
  decimal between 0.0 and 100.0.

Declare expectations for the sensor domain and the value range. Use seed 42.
```

Oracle: count==12 (2 series × 6 hourly points — implied, not stated, in the
prompt); sensor ∈ {temp, humidity}; value ∈ [0.0, 100.0]; engine `verified`
true.

### Gold-spec construction findings

The evaluator hit these hurdles before any model did (confirming they are
real schema hurdles): T2's child FK must be `{"kind": "script", "script":
"parent.id"}` — a randomly generated FK passes schema validation but fails
the per-parent-count acceptance check; the engine's `fix_hint` on the wrong
attempt names the `parent.` prefix. T4's memstore-completeness gate requires
BOTH a `{"kind": "identifier"}` role on the producer's id field AND a
`{"kind": "foreign_key", "parent_product": ..., "parent_field": ...}` role
on the consumer's id field — `ok: true` with all explicit checks passing
still yields `verified: false` until both are declared.

## 5. Results

✓tN = oracle-verified at turn N (locals) / attempt N (baseline). ✗ = failed
within budget. † = reclassified, see §7.2.

| Participant | T1 | T2 | T3 | T4 | T5 | Oracle score | Intent-true score |
|---|---|---|---|---|---|---|---|
| `gemma4:e4b` | ✓t2 | ✗ | ✗ | ✗ | ✗ | 1/5 | 1/5 |
| `gemma4:e4b-it-qat` | ✓t3 | ✗ | ✗ | ✗ | ✗ | 1/5 | 1/5 |
| `qwen3.5:9b-mlx` | ✓t4 | ✗ | ✗ | ✗ | ✗ | 1/5 | 1/5 |
| `ministral-3:8b` | ✓t5 | ✗ | ✓t4 | ✗ | ✗ | 2/5 | 2/5 |
| `qwen3-coder:30b-a3b` | ✓t2 | ✗ | ✓t2 | ✓t7† | ✗ | 3/5 | 2/5 † |
| Claude Haiku (baseline) | ✓a1 | ✓a7 | ✓a2 | ✗ | ✓a3* | 4/5 | 4/5 |

\* T5 baseline: first submission engine-verified but oracle-failed (missing
`series_count: 2`, 6 rows instead of 12); repaired on overall attempt 3
after the oracle result was delivered as a follow-up message.

† T4 `qwen3-coder`: passed every pre-registered oracle check, but did not
build the required pipeline — reclassified in §7.2.

**On the true task intent, T4 was passed by nobody.**

## 6. What each agent actually did — full action sequences

Notation: `caps` = capabilities; `schema` = reference scaffold;
`ref(c/k)` = reference authoring --category c --kind k; `SUBMIT` = scaffold
submission; `(stall)` = a turn with no tool call emitted.

```text
gemma4:e4b            T1 PASS t2  SUBMIT > SUBMIT
gemma4:e4b            T2 FAIL     SUBMIT > (stall) > (stall) > (stall) > schema > (stall) > (stall) > SUBMIT
gemma4:e4b            T3 FAIL     (stall) > (stall) > (stall) > SUBMIT > SUBMIT > SUBMIT > SUBMIT > SUBMIT
gemma4:e4b            T4 FAIL     (stall) > (stall) > SUBMIT > SUBMIT > SUBMIT > SUBMIT > SUBMIT > (stall)
gemma4:e4b            T5 FAIL     (stall) > (stall) > (stall) > SUBMIT > SUBMIT > SUBMIT > SUBMIT > SUBMIT

gemma4:e4b-it-qat     T1 PASS t3  (stall) > SUBMIT > SUBMIT
gemma4:e4b-it-qat     T2 FAIL     schema > (stall) x5 > SUBMIT > (stall)
gemma4:e4b-it-qat     T3 FAIL     (stall) > (stall) > SUBMIT > SUBMIT > (stall) > SUBMIT > (stall) > (stall)
gemma4:e4b-it-qat     T4 FAIL     (stall) > ref(field/increment) > (stall) > (stall) > SUBMIT > (stall) x3
gemma4:e4b-it-qat     T5 FAIL     (stall) > ref(field/constant) > (stall) > (stall) > SUBMIT > SUBMIT > (stall) x2

qwen3.5:9b-mlx        T1 PASS t4  ref(field/increment) > ref(field/values) > ref(field/int_range) > SUBMIT
qwen3.5:9b-mlx        T2 FAIL     SUBMIT > schema > ref(product/generated) > ref(field/foreign_key) > caps > SUBMIT > SUBMIT > ref(product/generated) > SUBMIT
qwen3.5:9b-mlx        T3 FAIL     caps > 7x ref(...) > SUBMIT > schema > SUBMIT > SUBMIT > SUBMIT
qwen3.5:9b-mlx        T4 FAIL     6x ref/caps > SUBMIT > schema > SUBMIT > caps > SUBMIT
qwen3.5:9b-mlx        T5 FAIL     ref(product/time_series) > ref(field/increment) > caps > SUBMIT > schema > SUBMIT > ref(field/weighted) > SUBMIT

ministral-3:8b        T1 PASS t5  ref(field/) > SUBMIT > (stall) > ref(field/int_range) > SUBMIT
ministral-3:8b        T2 FAIL     8x ref(...) incl. all 5 expectation kinds > SUBMIT > SUBMIT
ministral-3:8b        T3 PASS t4  ref(field/values) > ref(product/) > SUBMIT > SUBMIT > SUBMIT > SUBMIT
ministral-3:8b        T4 FAIL     caps > 5x ref(...) incl. product/source > SUBMIT > SUBMIT
ministral-3:8b        T5 FAIL     7x ref(...) > SUBMIT

qwen3-coder:30b-a3b   T1 PASS t2  caps > schema > 4x ref(...) > SUBMIT          (all discovery batched turn 1)
qwen3-coder:30b-a3b   T2 FAIL     caps > schema > 6x ref(...) > 7x SUBMIT
qwen3-coder:30b-a3b   T3 PASS t2  caps > schema > 9x ref(...) > SUBMIT          (all discovery batched turn 1)
qwen3-coder:30b-a3b   T4 PASS t7† caps > schema > 4x ref(...) > SUBMIT > ref(field/increment) > ref(expectation/unique) > SUBMIT > ref(target/memstore) > SUBMIT
qwen3-coder:30b-a3b   T5 FAIL     caps > 3x ref(...) > SUBMIT > 2x ref(...) > SUBMIT > SUBMIT > SUBMIT > SUBMIT
```

Baseline command sequences (from each agent's own mandatory report):

```text
Haiku T1 PASS a1  ref(field/increment) > ref(field/int_range) > scaffold  (verified first try)
Haiku T2 PASS a7  ref(expectation/exact_count) > 7x scaffold (repair chain: min/max naming ->
                  per_parent_count needs nesting -> children array shape -> parent.id script ->
                  roles as objects -> verified)
Haiku T3 PASS a2  ref(field/weighted) > ref(field/pattern) > scaffold(fail: min/max + expectation
                  kind names) > scaffold (verified)
Haiku T4 FAIL     ref(sink/memstore) [invalid category] > ref(target) [invalid: kind missing] >
                  ~18 scaffold attempts; ended ok:true, verified:false (budget exceeded, see §7.1)
Haiku T5 PASS a3* ref(time_series/product) [invalid] > ref(product/time_series) > ref(expectation)
                  [invalid] > ref(expectation/allowed_values) > ref(expectation/range) >
                  scaffold (engine-verified, 6 rows, oracle-FAIL) > [oracle feedback delivered] >
                  scaffold (fail: expectation field name) > scaffold (verified, 12 rows)
```

## 7. The two T4 stories — the study's most important section

### 7.1 Why the baseline (Haiku) failed T4

Haiku built the **correct** pipeline architecture: `users` with a memstore
target, `user_audit` as `kind: source` reading `{"kind": "memstore", "id":
..., "product": "users"}`, script fields (`this.id` etc.) for the read-back
columns, and a top-level `foreign_key` expectation. Its final state:
`ok: true`, 9 acceptance checks passed, 0 failed — and `verified: false`,
because one derived check stayed *unevaluable*:

> memstore completeness requires exactly one explicit consumer FK role
> targeting a typed producer identifier; found 0

The missing piece is a **pair of field-level role declarations**: `{"kind":
"identifier"}` on the producer's id field, plus `{"kind": "foreign_key",
"parent_product": "users", "parent_field": "id"}` on the consumer's id
field. Haiku knew a role was needed and tried repeatedly — its own report
lists "roles as strings", "objects with `type`", "objects with `kind`" all
failing — but never landed the exact pair. Root cause, visible in its
ledger: both of its T4 discovery calls were invalid queries
(`--category sink --kind memstore`; `--category target` with no kind), so
**it never fetched a single field fragment in T4** — and the
`ForeignKeyRole`/`IdentifierRole` schemas live in every field fragment's
`json_schema.$defs`. It burned ~20 scaffold attempts (violating its
8-invocation budget) probing role syntax by trial and error against an
error message that names the requirement but not the syntax. The evaluator
hit the identical wall building the gold spec and found the answer the same
way any agent would have to: inside a field fragment's `$defs`.

Verdict: not a reasoning failure — an under-documented two-sided role
requirement whose syntax is only discoverable in a place T4's failing
participants never looked. This is the study's clearest actionable tooling
finding: the memstore-completeness diagnostic should state the required
role syntax, or `reference authoring` should offer a `source`/`role`
fragment that surfaces it directly.

### 7.2 Why `qwen3-coder`'s T4 "pass" is reclassified

Its turn-7 submission passed every pre-registered oracle check and the
engine's verification. But the document contains **no `kind: "source"`
product at all**: `user_audit` is a second *generated* product with field
definitions copied from `users` (same increment id 1–5, same values list,
same int_range), plus the identifier/FK role pair, plus its own memstore
target. Nothing is ever read back out of a memstore. The oracle was
satisfied because: both counts are 5; increment ids 1–5 trivially "reference"
each other; region/credit checks test domain membership, not row equality;
and the engine verified because no memstore *consumer* exists to trigger the
completeness gate. The intent — "read the users back OUT of that memstore" —
is unfulfilled.

There is no indication of deliberate gaming; the model plausibly modeled
"audit" as "a second table that looks like users". But the verdict stands:
**pre-registered-oracle pass, intent fail**, and the oracle itself carries
the defect (no `kind == source` check, no users↔audit row-equality check).
Both are one-line fixes for any re-run, and the honest score column above
carries the reclassification.

Together, 7.1 + 7.2 are one lesson from two directions: the engine's
`verified` flag under-constrains (T5 baseline, T4 qwen3-coder), and typed
oracles are artifacts with their own bug surface. Layered, mutually
checking gates — engine acceptance + intent oracle + (for anything
production-bound) row-level equality checks — are the indicated design.

## 8. Analysis beyond T4

- **Gradient by class, not size.** The three 8–9B generalists score
  identically (1/5, T1 only) with the same failure texture: high
  schema-error volume (`min`/`max` naming, discriminator confusion,
  invented attributes like `unique: true`) plus — uniquely in the Gemma
  family — massive stalling: 3–6 no-tool-call turns per failed task (see
  §6; `gemma4:e4b-it-qat` T2 stalled 6 of 8 turns). Ministral (2/5) and
  qwen3-coder (3/5 oracle / 2/5 intent) fail on single missing concepts,
  not volume.
- **T2 is the sharpest small-model discriminator.** Zero local passes. The
  recovery chain it demands (naming → nesting → FK-by-`parent.id` → role
  objects) has more steps than any small model's effective budget.
  `qwen3-coder` came closest: its final T2 submission failed only the
  FK-sample and engine-verified checks — one concept (`script: parent.id`)
  from passing. The baseline traversed the full chain in exactly 7 attempts.
- **Batched discovery is a budget multiplier.** `qwen3-coder` fetched
  capabilities + full schema + 4–9 fragments inside turn 1 on every task —
  that's why it could afford discovery *and* multiple repairs in 8 turns.
  No other local model batched.
- **T5 failed all locals** on two distinct causes: window/`series_count`
  shape errors (most), and one intent misread — `qwen3-coder` submitted
  `values: ["sensor1", "sensor2"]` for the sensor field (apparently parsing
  "2 parallel series" as two sensor names), stayed engine-verified, failed
  only the oracle's `sensor_domain` check, and did not act on that feedback
  across four further submissions.

## 9. Threats to validity

- **Single seed, single run per cell** — no reliability claim; the clean
  gradient is unreplicated. Seeds 42–46 are future work.
- **Baseline transport differs**, and its T4 budget violation means T4
  effort is not comparable (pass/fail is; it failed with ~2.5× budget).
- **Oracle-feedback asymmetry on T5**: locals in-loop, baseline post-hoc
  (reported as a3*, not a1).
- **The guided prompt was tuned on flat-task failures**, so local T1
  results are partially circular; T2–T5 are not (the prompt says nothing
  about children, memstore, roles, or windows).
- **The evaluator authored both golds and oracles**, and §7.2 proves this
  matters: one oracle had an exploitable gap despite the gold-gate protocol.
  Independent oracle review would be required for any stronger claim.
- **Q4 quantization** may understate every local model's FP16 capability.
- **Prompt-ambiguity confound in T5**: "2 parallel series" was demonstrably
  parseable as sensor names; the implied row count of 12 was never stated.

## 10. Conclusions

1. Under a guided prompt that fully solves flat records, **structural**
   complexity (nesting, pipelines, time windows) — not field-kind variety —
   is what separates small local models from a capable baseline.
2. Practical local-deployment rungs today: 8–9B generalists → flat
   single-product models only; agentic-tuned 8B → rich flat models; coding
   30B MoE → close to relational/pipeline but not across the line within
   tight budgets.
3. `verified: true` must not be the sole acceptance gate — for anyone. Both
   under-constraint specimens (missing `series_count`; look-alike instead
   of read-back) sailed through it.
4. Highest-leverage tooling fixes, in order: (a) make the
   memstore-completeness diagnostic state the required role syntax (it
   defeated the baseline and nearly everything else); (b) per-structural-
   family worked examples (flat/nested/pipeline/time-series) in agent-facing
   guidance — the single flat example transferred to nothing structural;
   (c) machine-derivable intent checks (e.g., "N parallel series" ⇒
   expected row count) surfaced by `scaffold` itself.

## 11. Reproduction

Harness `ollama_cli_eval_v4_ladder.py` and gold specs live in the session
scratchpad, uncommitted by this archive's evidence-outside-the-repo
convention; this document contains everything needed to rebuild them: the
verbatim system prompt (§3), verbatim task prompts and oracle definitions
(§4), tool-to-CLI mapping (§3), settings (seed 42, 8 turns, model-default
sampling, `num_ctx` 32768), and the gold-gate protocol (gold must reach
`verified: true` with deterministic replay; oracle must pass on gold;
both before any model runs). Repository state verification:

```bash
.venv/bin/pytest -q tests_ce/unit_tests/test_authoring tests_ce/unit_tests/test_docs \
  tests_ce/functional_tests/test_cli
.venv/bin/ruff check datamimic_ce
```
