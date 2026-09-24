# Additional Qwen3-Coder category-discovery rerun — 2026-07-16

Append-only follow-up to
[`2026-07-15-t1-t5-challenge-ladder.md`](2026-07-15-t1-t5-challenge-ladder.md).
The task text, system prompt, four CLI tool schemas, eight-turn cell budget,
and typed oracle are unchanged. This run measures the generic authoring
contract change that makes a typed category request (for example,
`reference authoring --category field`) return its schema-owned variants
instead of failing because no individual kind was selected.

✓tN = oracle-verified at turn N. ✗ = failed within the eight-turn budget.

| Participant | T1 | T2 | T3 | T4 | T5 | Oracle score | Intent-true score |
|---|---|---|---|---|---|---|---|
| `qwen3-coder:30b-a3b` | ✓t2 | ✓t4 | ✓t4 | ✓t6 | ✗ | 4/5 | 4/5 |

## Run record

- Code commit: `30a58a4c55613d01aa2c70001269b2ddbd886560`.
- Model: `qwen3-coder:30b-a3b-q4_K_M`, local Ollama ID `06c1097efce0`,
  18 GB, GGUF `Q4_K_M`, 30.5B total / 8 active experts. Ollama advertised
  `completion` and `tools`; the harness therefore sent native tool schemas
  and did not send a `think` option.
- Inference options: `num_ctx=32768`, `seed=42`. Stored sampling defaults:
  temperature 0.7, top-k 20, top-p 0.8, repeat penalty 1.05.
- Preflight: passed with the exact chat/profile before any cell was scored.
  There were no HTTP errors, unsupported options, retries, or excluded cells.
- Raw ledger and machine-written summary remain outside the repository at
  `/private/tmp/datamimic-ladder-rerun-20260716T093444Z/`.

## Interpretation and comparison boundary

T3 changed from failure to `✓t4`: the model's prior category-only discovery
call had consumed a turn on a transport error, whereas the new typed listing
let it discover field variants and submit early enough to repair. T4 is
intent-true: the oracle additionally observed a `source` product, a memstore
binding, and equality of producer/readback captures.

This is an improvement over the immediately preceding controlled run at
commit `2e19de4` under the same model tag, tool set, turn limit, context
window, and inference seed (3/5: T1, T2, T4). It also exceeds the original
ladder's 3/5 oracle score and its 2/5 intent-true score. It is not a causal
comparison against the original row: that historical record did not preserve
an Ollama inference seed, and the code commit intentionally changed. No claim
is made about T5; it still failed within budget.
