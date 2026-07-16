# Seeded CLI authoring challenge-ladder rerun — 2026-07-16

Additional record for the five-rung CLI-only authoring ladder in
[`2026-07-15-t1-t5-challenge-ladder.md`](2026-07-15-t1-t5-challenge-ladder.md).
It evaluates the authoring diagnostics branch at `52421c4` after D1–D7.

## Decision

The first attempted rerun was **not scored**. It fixed `num_ctx` but omitted
Ollama's inference `options.seed`; a lower score from that run would not be
evidence of a model regression. Two early rows also sent `think: true` to
models that do not advertise `thinking`, producing HTTP 400 responses. Those
partial rows were discarded, not converted to failures.

The score table below is the only local result for this record. Every exact
profile passed preflight, used native Ollama tool calling, set
`options={"num_ctx": 32768, "seed": 42}`, and completed without an access
error. The Intent Model itself also uses seed 42. Those are separate seeds.

## Frozen protocol

- Commit: `52421c4aaed75efc969e86d51ea0d428abb3e27b`.
- Tasks, system prompt, four tool schemas, and eight-turn cell budget:
  unchanged from the 2026-07-15 record. The typed oracle preserves the
  original intent checks and additionally requires the D1 source/read-back
  contract for T4 and D7 compiler-derived row-count evidence for T5.
- Transport: `/api/chat`, `stream: false`, native `tools`; assistant
  `tool_calls` and tool-result messages were retained in the conversation.
- Context/inference options: `num_ctx=32768`, `seed=42`; each model otherwise
  kept its stored sampling defaults.
- Thinking: sent only to `gemma4:e4b`, `gemma4:e4b-it-qat`, and
  `qwen3.5:9b-mlx`, whose installed manifests advertise `thinking`.
- Prompt SHA-256: `6c4d33cc64e6e129d42c044988c907306faaa7a72ef402fa2787d94790a0d176`.
  Task SHA-256: `084f7dc9860018238146ba4d1ffbb052b49242ce2e78cc02be8f9619c9b08e70`.
  Tool-schema SHA-256:
  `ba01c8b3d403c9edc5fe17ca2ccf94dfe4abc413588ed6273fb3eba37b3dbffd`.

## Installed local profiles

All five profiles declared `tools`. Model tag/digest and stored parameters
were captured with `ollama list` and `ollama show` before the run.

| Model | Digest | Quantization | Thinking | Stored sampling defaults |
|---|---|---|---|---|
| `gemma4:e4b` | `c6eb396dbd59` | Q4_K_M | yes | temperature 1, top_p .95, top_k 64 |
| `gemma4:e4b-it-qat` | `ee6656371218` | Q4_0 | yes | temperature 1, top_p .95, top_k 64 |
| `qwen3.5:9b-mlx` | `203e30078279` | nvfp4 | yes | temperature 1, top_k 20, top_p .95, min_p 0, presence_penalty 1.5, repeat_penalty 1 |
| `ministral-3:8b-instruct-2512-q4_K_M` | `1922accd5827` | Q4_K_M | no | temperature .15 |
| `qwen3-coder:30b-a3b-q4_K_M` | `06c1097efce0` | Q4_K_M | no | temperature .7, top_k 20, top_p .8, repeat_penalty 1.05 |

## Results and comparison status

This run is a valid **post-change benchmark**, but it is not yet a controlled
before/after measurement of D1–D7: the 2026-07-15 record did not fix the
Ollama inference seed, and this run strengthens T4/T5 with the new D1/D7
contracts. Therefore a score difference must not be attributed to the code
changes. A valid improvement claim requires an additional run of the
pre-change commit under this exact profile and oracle.

✓tN means that the typed oracle passed on turn N; ✗ means no oracle pass
within the eight-turn budget. ✓ for an agent row means its reported verified
submission passed the post-run semantic check. All local-Ollama preflights
passed.

| Participant | Execution mode | T1 | T2 | T3 | T4 | T5 | Score |
|---|---|---|---|---|---|---|---|
| `gemma4:e4b` | native Ollama | ✓t2 | ✗ | ✗ | ✗ | ✗ | 1/5 |
| `gemma4:e4b-it-qat` | native Ollama | ✗ | ✗ | ✗ | ✗ | ✗ | 0/5 |
| `qwen3.5:9b-mlx` | native Ollama | ✗ | ✗ | ✓t4 | ✗ | ✗ | 1/5 |
| `ministral-3:8b-instruct-2512-q4_K_M` | native Ollama | ✗ | ✗ | ✓t5 | ✗ | ✓t5 | 2/5 |
| `qwen3-coder:30b-a3b-q4_K_M` | native Ollama | ✓t2 | ✓t5 | ✗ | ✗ | ✗ | 2/5 |
| Luna | isolated CLI agent | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |
| `gpt-5.4-mini` | isolated CLI agent | ✓ | ✓ | ✓ | ✓ | ✓ | 5/5 |

The D1–D7 contracts are exercised by successful T2 nested-FK validation and
T5 compiler-derived row-count evidence. No local participant passed T4, so
the memstore role-pairing/read-back rung remains the dominant gap.

## Agent-row caveat

Spark was removed from the requested comparison before scoring and has no row
in this report. The host did not offer a model named GPT-4 mini; the requested
mini-agent check therefore used the available `gpt-5.4-mini`, which is not
claimed to be an equivalent model.

Luna and `gpt-5.4-mini` each received one isolated, context-free task prompt,
the same CLI-only constraint and eight-invocation budget, and no repository
read/write permission. Both reported `verified=true` submissions for T1–T5;
a post-run check of their final intent documents found every task-specific
semantic condition satisfied (5/5 each). They are displayed in the common
table because they were requested comparison participants, while their
different transport and in-loop oracle feedback remain explicit in the
`Execution mode` column.

## Interpretation and artifacts

This is one fixed inference seed, not a reliability estimate. The old and new
rows are not an improvement comparison until the pre-change commit has been
run under this exact profile and strengthened oracle. A future reliability
claim additionally needs multiple pre-registered inference seeds.

Scratch-only machine evidence is retained outside the repository at
`/private/tmp/datamimic-ladder-rerun-20260716T070951Z/` (append-only ledger
and summary). Earlier unseeded/configuration-error attempts were retained
there for audit but deliberately excluded from the table. No transcript,
generated descriptor, provider identifier, or runtime output is committed.
