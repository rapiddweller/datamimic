# Canonical authoring diagnostic — 2026-07-15

This curated record captures a single-seed diagnostic against commit `bbb9074`.
It is not a portable benchmark suite, a model ranking, or a reliability claim.
Raw model artifacts, transcripts, provider request identifiers, and runtime
outputs are intentionally not tracked.

## Contract and method

The model-authored artifact was always `model.dm.json`. Evaluated models could
use bounded CLI wrappers for help, capabilities, typed `reference authoring`,
and `scaffold`. A cell passed only when scaffold returned `ok=true` and
`verified=true` with smoke export and deterministic replay, followed by an
independent business-intent oracle. Raw XML lint and dry-run were evaluator-only
checks, never an alternate authoring path.

Conditions were paired per model:

- **C0:** generic bounded tool loop without DATAMIMIC workflow guidance.
- **C1:** typed discovery, structured repair, no unchanged failed call, and
  terminal stop on the first verified scaffold.

Tasks:

- **T1 flat:** five seeded rows, globally unique integer ID, exact A/B/C domain,
  score 10–20, JSON, smoke export, and replay.
- **T2 relational:** four parents with two directly nested children each, FK,
  local sequence 1/2, globally unique composite child ID, and amount range.
- **T3 integrated:** eight customers, sixteen orders, eight ordered audit rows,
  FK, local/global identity, memstore read-back, and exposure checks.

Each model cell used seed 42, at most 10 turns and 20 tool calls, up to 2,000
completion tokens per turn, 65,536 context tokens, 240 seconds per answer, and
900 seconds per cell. The temporary harness passed a 20/20 zero-inference
self-test, including verified gold T1/T2/T3 artifacts and negative oracle
mutations.

## Access gate

Access failures are excluded from semantic denominators.

| Model | Access/native tool | Classification |
|---|---|---|
| `gemma4:31b-cloud` | pass | admitted |
| `qwen3.5:cloud` | HTTP 403 before inference | access failure; no semantic result |
| `qwen3-coder-next:cloud` | pass | admitted |
| `qwen3-coder:480b-cloud` | pass | admitted |
| `gemma4:31b` | pass | admitted |
| `ministral-3:8b-cloud` | pass | admitted |

Five of six candidates were accessible. The Qwen 3.5 response is no quality
evidence.

## T1 paired result

| Model | C0 | C1 | Observed effect |
|---|---|---|---|
| Gemma Cloud | pass, verified turn 4 | pass, verified turn 3 | one turn/tool saved |
| Qwen Coder Next | pass, verified turn 5 | fail, 10 discovery calls | pass changed to fail |
| Qwen Coder 480B | fail, no resubmission | pass, verified turn 10 | fragile late pass |
| Gemma local | fail, repair budget | fail, repair budget | no outcome change |
| Ministral 8B | pass, verified turn 2 | pass, verified turn 4 | more discovery and tools |

Both conditions passed 3/5. C1 added 12 tool calls and 41,808 prompt tokens
without adding an aggregate pass. This supports a diagnostic hypothesis that
open-ended "discover first" guidance can cause discovery fixation; one paired
seed does not establish causality.

## T2/T3 promotion

Only the three T1 C1 passes entered T2. Gemma Cloud, Qwen Coder 480B, and
Ministral 8B all ended with `model_budget`; none reached verified scaffold.
Therefore no relational oracle ran. T3 was intentionally not run because the
predeclared promotion gate required a verified T2 artifact.

This is 0/3 for T2 and no data for T3, not evidence that T3 failed.

## Lunar clean-room reference

A context-free Lunar agent used only the CLI, authored exact T1 intent, and
reached verified scaffold on call 10 of 10. Independent adjudication passed
lint, bounded execution, all seven T1 business checks, replay, and smoke export;
the adjudicated XML exactly matched scaffold output.

The ordered ten-call sequence existed only in the agent-authored report. There
was no machine-generated, timestamped, hashed call ledger. Semantic correctness
is independently established; process provenance is not cryptographically
complete.

## Decisions

- **GO:** canonical scaffold/acceptance when a correct T1 intent reaches it.
- **NO-GO:** current C1 guide as production default; it cost more with no pass
  gain in this sample.
- **NO-GO:** unattended relational T2 with the evaluated prompt/tool surface.
- **NO DATA:** T3 and Qwen 3.5 semantic quality.
- **NO-GO:** model ranking, reliability, or size-causality claims from seed 42.

## Ranked follow-up

1. Require at most one query-list or narrow fragment on turn 1 and a complete
   best-effort scaffold by turn 2.
2. Enforce a hard discovery budget: one query listing plus two narrow fragments
   before the first scaffold.
3. Encode the `category`/`kind` dependency in the tool schema.
4. Project one canonical typed relational example from Intent Model and rule
   facts; do not maintain a handwritten parallel schema.
5. Return a complete corrected subtree for nested structural errors.
6. Preserve exact path, rejected value, allowed fields, corrected fragment,
   rule ID, and fix hint for every failed CLI call.
7. Generate a timestamped call ledger with argument/stdout/stderr hashes,
   terminal verified index, post-verified count, and SHA-256 cell manifest.
8. Rerun paired seeds 42–46. Promote at least 4/5 verified plus oracle passes
   at T1 and T2; run T3 only for T2-promoted models. Treat five seeds as a
   screen, not a release reliability claim.
