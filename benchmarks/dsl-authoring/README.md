# Authoring evaluation archive

This directory contains curated evaluation records, not an executable benchmark
harness. DATAMIMIC currently has no committed portable harness for canonical
agent authoring.

## Records

- [`evaluations/2026-07-15-t1-t5-challenge-ladder.md`](evaluations/2026-07-15-t1-t5-challenge-ladder.md)
  — the original five-rung difficulty ladder (flat →
  relational → mixed fields → memstore pipeline → time series) across five
  local models with a Claude Haiku baseline. Self-contained and
  paper-structured: verbatim prompts, per-cell action sequences, failure
  taxonomy, an honest oracle-loophole reclassification, and a
  threats-to-validity section. Supersedes the earlier compact-capabilities
  diagnostic on this branch (its essential findings are folded into the
  ladder paper's background section; full text remains in git history).
- [`evaluations/2026-07-16-t1-t5-challenge-ladder-seeded-rerun.md`](evaluations/2026-07-16-t1-t5-challenge-ladder-seeded-rerun.md)
  — additional rerun after the authoring diagnostics changes. It fixes the
  Ollama inference seed, pins the context window, preflights each exact model
  profile, records model digests and capabilities, and keeps the requested
  Luna and `gpt-5.4-mini` agent checks separate from the native-Ollama matrix.
  It supersedes any score comparison based on the unseeded diagnostic reruns.

The records deliberately omit generated models, transcripts, provider request
identifiers, and runtime outputs. Those artifacts belong in a system temporary
directory and must not be committed.

## Contract for a future canonical harness

A future harness must:

- retain `model.dm.json` as the authored Intent Model SPOT;
- invoke authoring through the CLI or the same canonical service use case, never
  by directly composing compiler, linter, or dry-run implementation modules;
- stop on the first scaffold result with `verified=true`;
- evaluate business intent with a typed oracle over canonical scaffold evidence;
- keep access failures separate from semantic failures;
- record multiple seeds, explicit budgets, and a machine-generated hashed call
  ledger before making reliability claims; and
- write all generated evidence outside the repository.
