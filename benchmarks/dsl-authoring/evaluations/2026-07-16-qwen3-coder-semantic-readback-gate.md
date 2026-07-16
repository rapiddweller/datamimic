# Additional Qwen3-Coder semantic-readback rerun — 2026-07-16

Append-only follow-up to
[`2026-07-16-qwen3-coder-category-discovery.md`](2026-07-16-qwen3-coder-category-discovery.md).
The task text, system prompt, four CLI tool schemas, eight-turn cell budget,
typed oracle, model digest, context window, inference seed, and stored sampling
defaults are unchanged. This run measures a generic semantic-contract change:
a memstore readback that regenerates a same-named stored field may complete its
bounded run, but it cannot claim `verified=true` until it references the stored
field.

✓tN = oracle-verified at turn N. ✗ = failed within the eight-turn budget.

| Participant | T1 | T2 | T3 | T4 | T5 | Oracle score | Intent-true score |
|---|---|---|---|---|---|---|---|
| `qwen3-coder:30b-a3b` | ✓t2 | ✓t4 | ✓t4 | ✓t6 | ✗ | 4/5 | 4/5 |

## Run record

- Code commit: `ba3270371e5b15d1301a35b5f27ce799df498976`.
- Model: `qwen3-coder:30b-a3b-q4_K_M`, local Ollama ID `06c1097efce0`,
  18 GB, GGUF `Q4_K_M`, 30.5B total / 8 active experts. Ollama advertised
  `completion` and `tools`; the harness sent native tool schemas and omitted
  `think`.
- Inference options: `num_ctx=32768`, `seed=42`. Stored sampling defaults:
  temperature 0.7, top-k 20, top-p 0.8, repeat penalty 1.05.
- Preflight: passed with the exact chat/profile before scoring. There were no
  HTTP errors, unsupported options, retries, or excluded scored cells.
- Raw ledger and machine-written summary remain outside the repository at
  `/private/tmp/datamimic-ladder-rerun-20260716T105907Z/`.

## Interpretation and comparison boundary

T4 again reaches an intent-true model at turn 6. The turn-5 attempt carried a
producer identifier and consumer foreign-key role but independently regenerated
the remaining same-named fields. The rule catalog now marks that generic
memstore readback-integrity finding as verification-blocking, so the agent
received `verified=false`, repaired the fields to direct scripts, and passed
the capture-equality oracle. This is a semantic contract, not a T4-specific
branch: producer binding comes from the compiler plan and the rule applies to
every resolved memstore relationship.

T5 remains a normal oracle failure: the agent models `temp`/`humidity` as a
new `measurement_type` field rather than the requested `sensor` field. The
bounded run and explicit expectations verify, but the task's named business
dimension is not satisfied. No benchmark-specific rule was added for that
natural-language interpretation.

This row preserves the prior valid 4/5 score under the same Qwen profile while
making the T4 `verified` certificate stricter and truthful. A full,
preflight-passing 3/5 diagnostic candidate at `bc3b02a` exposed the missing
semantic gate; it is retained only in the external ledger
`/private/tmp/datamimic-ladder-rerun-20260716T104529Z/` and is not promoted as
a curated comparison row. This report makes no claim of a score increase.
