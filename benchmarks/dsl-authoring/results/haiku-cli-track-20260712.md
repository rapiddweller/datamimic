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
needed only slightly more iterations on average (nested_reviews took 2; every
other task was green first try) and zero agents mentioned missing MCP or fell
back to grepping parser source — all discovered `datamimic reference` /
`datamimic --help` / `datamimic capabilities` unprompted.

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
| qwen3.5:9b | scored normally | 0/6 | 0/6 |
| mistral:latest | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| qwen2.5-coder:1.5b | broken manifest, fixed by re-pull mid-session (not re-run) | n/a | n/a |
| deepseek-r1:7b-qwen-distill-q4_K_M | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| gemma4:26b | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |
| qwen3.5:35b-a3b-q8_0 | broken manifest (HTTP 400, all 6 tasks) | n/a | n/a |

qwen3.5:9b (full per-task detail in `ollama-extended-loop.json`): despite
having tool/thinking capability flags in `ollama show`, it did not converge
within 3 iterations on any task in this run.

Reference: Haiku 4.5 track (`haiku-track-20260704.md`): bare 0/6, MCP tool loop
6/6 intent-correct. CLI-only tool loop (this file, above): 6/6 intent-correct.
The gap between small local models and Haiku 4.5 in the diagnostics-loop
condition remains the dominant factor — larger than MCP vs. CLI.
