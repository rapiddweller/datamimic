# Three-model test + best-of-N harness fix, 2026-07-13

Requested: test `qwen2.5-coder:1.5b`, `deepseek-r1:7b-qwen-distill-q4_K_M`, `gemma4:31b`
under the `--loop` condition (6 iterations, post-DM105/DM401/DM402-fix linter) to discuss
success/improvement rate. `deepseek-r1`'s local manifest was stale again (same class of issue
as the other Ollama models earlier this session) and was re-pulled first.

## Results (best-of-N scoring, see harness fix below)

| model | params | runs (score≥1) | intent-correct (score=2) |
|---|---|---|---|
| gemma4:31b | 31.3B | **6/6** | **6/6** |
| qwen2.5-coder:1.5b | 1.5B | 4/6 | 2/6 |
| deepseek-r1:7b-qwen-distill-q4_K_M | 7.6B | 1/6 | 0/6 |
| *(reference)* Haiku 4.5, MCP or CLI-only | — | 6/6 | 6/6 |

`gemma4:31b` is up from 5/6 in the pre-tooling-fix matrix (`latest.md`) — its only prior miss,
`memstore_pipeline`, now converges in 2 iterations, exactly the failure mode the DM105/DM401/
DM402 fix (see `haiku-cli-track-20260712.md`) targeted. It now matches Haiku 4.5's intent-correct
rate under this condition.

`qwen2.5-coder:1.5b` (1.5B) and `deepseek-r1:7b-distill` (7.6B) both still fail broadly, and not
mainly on DSL semantics — `deepseek-r1` hit `NO_XML`/`DM001` (malformed or absent XML) on 3 of 6
tasks, i.e. it can't reliably produce well-formed output at all after 6 rounds of lint/dry-run
feedback. The tooling fix helps models that are close (gemma4:31b, and qwen3.5:9b from the prior
session's retest) but doesn't rescue models that fail at the mechanical level.

## Harness fix: best-of-N instead of last-of-N (`bench.py`)

`run_loop_cell` reported the score of the LAST iteration, discarding real progress if a later
self-correction attempt regressed. First identified last session from `reproducible_orders`'
1→0 regression under the earlier 3→6 iteration-budget bump; this session's `deepseek-r1` run
produced a second, cleaner example:

```
nested_reviews:
  iter3: score=0 (lint error)
  iter4: score=1 (runs, wrong intent)   <- actual best attempt
  iter5: score=0 (NO_XML — collapsed back to malformed output)
```

Fixed: `run_loop_cell` now selects the best-scoring iteration (ties broken by fewest error
`rule_ids`, then earliest index — rewards fast, cheap convergence), and reports `last_score` +
`best_iteration` alongside `score` for transparency. Verified via `--selftest` (4 synthetic
best-of-N cases + a tie-break case, plus the existing 7 golden-descriptor checks, all pass).

**Retroactively applied to every existing loop-mode result file** (`rescored_best_of_n` key
marks which ones) by re-deriving `score`/`rule_ids`/`detail` from the `iteration_details` each
run already recorded — no new Ollama calls. Net effect across all loop-mode runs collected so
far:

| model | runs (last-of-N) | runs (best-of-N) | intent-correct (either) |
|---|---|---|---|
| deepseek-r1:7b-distill | 0/6 | 1/6 | 0/6 (unchanged) |
| qwen2.5-coder:1.5b | 2/6 | 4/6 | 2/6 (unchanged) |
| qwen3.5:9b (3 runs, n=18) | 7/18 | 8/18 | 6/18 (unchanged) |
| gemma4:31b | 11/11 | 11/11 | 11/11 (unchanged) |
| qwen2.5:7b | 2/6 | 2/6 | 2/6 (unchanged) |

**Honest reading**: best-of-N did not manufacture a single new intent-correct (score=2) result
in any run collected so far — it only recovers partial credit (score 1, "runs but wrong intent")
that a later, worse attempt had overwritten. It's a benchmark-honesty fix, not a capability
lift: it makes "runs" numbers reflect what a model actually produced at its best, and it matters
more for weaker models (which regress more often) than for gemma4:31b, which barely regresses at
all under this condition.

## Where this leaves the "success rate / improvement rate" discussion

- **Raw model capability now dominates.** The DM105/memstore tooling fix rescued a
  capable-but-imperfect model (gemma4:31b, qwen3.5:9b) from a specific dead end; it does nothing
  for models that can't produce valid XML in the first place (deepseek-r1, qwen2.5-coder:1.5b).
  Further tooling polish has a shrinking return on this end of the model range.
- **The best-of-N fix is now permanent infrastructure** — every future loop-mode run benefits
  automatically, and it's the honest baseline going forward.
- Two Fable-flagged harness ideas remain unimplemented and could plausibly help the *weak* end
  specifically: thrash/repeat detection (abandon and restart fresh instead of burning iterations
  on a stuck model — direct evidence in `deepseek-r1`'s `memstore_pipeline`, which held steady at
  `DM103` for 3 straight iterations before finally regressing further), and `scaffold.py`
  (JSON-spec → guaranteed-valid-XML, sidesteps free-form XML generation entirely) — the more
  structurally relevant lever for models failing at the XML-well-formedness level, not the DSL
  level.
