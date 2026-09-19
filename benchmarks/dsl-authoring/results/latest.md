## qwen2.5:7b

| task | P0_bare | P1_intent_table | P2_cheatsheet | P3_fewshot | loop |
|---|---|---|---|---|---|
| weighted_country | 0 | 0 | 0 | 2 | 0 |
| nested_reviews | 0 | 0 | 0 | 1 | 2 |
| reproducible_orders | 0 | 0 | 2 | 2 | 2 |
| memstore_pipeline | 0 | 0 | 0 | 0 | 0 |
| timeseries | 0 | 0 | 0 | 0 | 0 |
| branch_fk | 0 | 0 | 0 | 2 | 0 |

P0_bare: intent-correct 0/6, runs 0/6 | P1_intent_table: intent-correct 0/6, runs 0/6 | P2_cheatsheet: intent-correct 1/6, runs 1/6 | P3_fewshot: intent-correct 3/6, runs 4/6 | loop: intent-correct 2/6, runs 2/6

Static best (P3_fewshot): intent-correct 3/6 vs loop: 2/6.
Loop iterations used: 1 iteration: 1 tasks, 2 iterations: 1 tasks, 3 iterations: 4 tasks.

## gemma4:31b

| task | P0_bare | P1_intent_table | P2_cheatsheet | P3_fewshot | loop |
|---|---|---|---|---|---|
| weighted_country | 0 | 0 | 2 | 2 | 2 |
| nested_reviews | 0 | 0 | 2 | 1 | 2 |
| reproducible_orders | 0 | 0 | 2 | 2 | 2 |
| memstore_pipeline | 0 | 0 | 0 | 0 | 0 |
| timeseries | 0 | 0 | 0 | 0 | 2 |
| branch_fk | 0 | 0 | 0 | 0 | 2 |

P0_bare: intent-correct 0/6, runs 0/6 | P1_intent_table: intent-correct 0/6, runs 0/6 | P2_cheatsheet: intent-correct 3/6, runs 3/6 | P3_fewshot: intent-correct 2/6, runs 3/6 | loop: intent-correct 5/6, runs 5/6

Static best (P2_cheatsheet): intent-correct 3/6 vs loop: 5/6.
Loop iterations used: 1 iteration: 5 tasks, 3 iterations: 1 tasks.

Reference: Haiku 4.5 track (haiku-track-20260704.md): bare 0/6, tool loop 6/6 intent-correct.
