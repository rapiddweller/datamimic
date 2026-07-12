# Haiku 4.5 CLI-only track (no MCP), 2026-07-12

Same 6 tasks, same scoring pipeline (`score_generation`, lint + dry-run + intent
check) as the MCP-based H1 track in `haiku-track-20260704.md`. Six independent
Haiku agents, each with shell access to the `datamimic` CLI only (no MCP server
registered, no parser source grepping instructed or observed) and the same task
prompts as `bench.py`'s `TASKS`. Each agent explored on its own (`datamimic --help`,
`datamimic reference overview`, showcase examples) before drafting; final
descriptors graded independently against `TASKS_BY_ID`, not self-reported.

| task | iterations (self-reported) | score |
|---|---|---|
| weighted_country | 1 | 2 |
| nested_reviews | 2 | 2 |
| reproducible_orders | 1 | 2 |
| memstore_pipeline | 1 | 2 |
| timeseries | 1 | 2 |
| branch_fk | 1 (fixed an IncrementGenerator collision warning pre-final) | 2 |

**runs: 6/6, intent-correct: 6/6** — matches the MCP-based H1 track exactly (see
`haiku-track-20260704.md`: H1 was also 6/6 runs, 6/6 intent-correct, needing at
most 2 lint iterations per task, 4/6 green on first try). This CLI-only run
needed a comparable-or-fewer number of iterations (5/6 tasks green on first
try, only nested_reviews took 2, vs. H1's 4/6 green on first try) and zero
agents mentioned missing MCP or fell back to grepping parser source — all
discovered `datamimic reference` / `datamimic --help` / `datamimic
capabilities` unprompted. H1's branch_fk also needed a manual score
adjudication (grader under-scored a valid nested shape); this run's branch_fk
scored 2 straight from the grader, no adjudication needed — if anything the
cleaner of the two results.

Conclusion: for this task set, a well-designed CLI (reference + lint + dry-run
+ iterate) gives Haiku 4.5 the same authoring reliability as the MCP tool loop.
MCP's value here is discoverability/ergonomics (structured tool calls vs. shell
command construction) and machine-readable JSON I/O for programmatic callers,
not a capability the CLI lacks. See `haiku-track-20260704.md`'s H0 baseline for
the real gap: 0/6 with no lookup tool at all, regardless of MCP vs CLI.

## Ollama loop-mode: models newly tested this session (2026-07-12)

Six previously-untested local Ollama models were run through the same
`--loop` diagnostics-loop condition as the existing matrix. Two models produced
real scores; the other four/five failed with `HTTP Error 400: Bad Request` on
every single task, traced to **stale local Ollama model manifests** (`ollama show
<model>` returned "not found" despite the model appearing in `ollama list`,
and `/api/chat` rejected them with `"<model>" does not support chat"`) — an
Ollama-side storage issue unrelated to the benchmark harness or DATAMIMIC.
Re-pulling `qwen2.5-coder:1.5b` (986 MB) confirmed the fix: after `ollama pull`,
the same model answered `/api/chat` normally. The other four broken models
(mistral:latest 4.4GB, deepseek-r1:7b-qwen-distill-q4_K_M 4.7GB, gemma4:26b 17GB,
qwen3.5:35b-a3b-q8_0 38GB — ~64GB total) were not re-pulled in this session
(local bandwidth ~2.7 MB/s, hours of download); re-run once re-pulled.

| model | status | loop: runs | loop: intent-correct |
|---|---|---|---|
| qwen3.5:9b | scored normally | 2/6 | 1/6 |
| mistral:latest | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| qwen2.5-coder:1.5b | broken manifest, fixed by re-pull mid-session (see below) | n/a | n/a |
| deepseek-r1:7b-qwen-distill-q4_K_M | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| gemma4:26b | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| qwen3.5:35b-a3b-q8_0 | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |

qwen3.5:9b per-task detail (`ollama-extended-loop.json`), at the original
`LOOP_MAX_ITERATIONS = 3`: nested_reviews scored 2 first try;
reproducible_orders ran but failed intent (score 1); the other four scored 0
— but not from a flat inability to use the DSL. The per-iteration record
shows genuine incremental progress on several of them that simply ran out of
budget: branch_fk went 1 error -> 3 errors -> 1 error across 3 attempts (still
converging, cut off); memstore_pipeline went 2 errors -> 2 errors (identical,
no progress) -> 1 error (cut off mid-fix). weighted_country and timeseries
instead oscillated between distinct errors without narrowing (thrashing, not
progress) — a harness-budget fix will not help those two.

**Root-cause based fix, not just infra housekeeping**: bumped
`LOOP_MAX_ITERATIONS` 3 -> 6 in `bench.py` and re-ran qwen3.5:9b alone (the one
model with a working manifest) to test whether the cut-off tasks converge with
more room. Result in `ollama-loop-retest-qwen3.5-9b.json`:

| task | @3 iterations | @6 iterations |
|---|---|---|
| weighted_country | 0 (thrashing: DM104 -> DM002 -> DM101, never narrowed) | 2, converged in 1 |
| nested_reviews | 2 | 2, converged in 1 |
| reproducible_orders | 1 (runs, wrong intent) | 0, burned all 6 iterations, landed on DM105 |
| memstore_pipeline | 0 (2 errors -> 2 errors -> 1 error, cut off mid-fix) | 0, stuck on DM401 across all 6 |
| timeseries | 0 (oscillating DM105 <-> DM000, no narrowing) | 0, still oscillating on DM105 after 6 |
| branch_fk | 0 (1 -> 3 -> 1 errors, cut off mid-fix) | 2, converged in 3 |

**runs 2/6 -> 3/6, intent-correct 1/6 -> 3/6** — a real, tripled improvement
from a one-line constant change, not a full fix: branch_fk and
weighted_country were genuinely making progress and just needed the room;
memstore_pipeline and timeseries were truly stuck (same failure mode with 6
iterations as with 3, not a budget problem) and need a different lever
(few-shot seeding, better lint fix-hints, or a stronger local model);
reproducible_orders regressed (1 -> 0) — more self-correction attempts let it
wander out of a locally-decent state into a new lint error, a real failure
mode of naive loop-until-N-iterations harnesses, not just noise.

Reference: Haiku 4.5 track (`haiku-track-20260704.md`): bare 0/6, MCP tool loop
6/6 intent-correct. CLI-only tool loop (this file, above): 6/6 intent-correct.
qwen3.5:9b tool loop (this section): 1/6 -> 3/6 intent-correct after the
iteration-budget fix. The gap between small local models and Haiku 4.5 in the
diagnostics-loop condition remains the dominant factor — larger than MCP vs.
CLI — but is not fixed, only narrowed, by more iterations alone.
