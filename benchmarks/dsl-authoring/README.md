# Authoring evaluation archive

This directory contains curated evaluation records, not an executable benchmark
harness. DATAMIMIC currently has no committed portable harness for canonical
agent authoring.

## Records

- [`evaluations/2026-07-15-canonical-authoring.md`](evaluations/2026-07-15-canonical-authoring.md)
  documents the current `model.dm.json` and scaffold diagnostic.
- [`evaluations/2026-07-15-haiku-cli-authoring.md`](evaluations/2026-07-15-haiku-cli-authoring.md)
  separates independently checked business delivery from canonical authoring
  and raw-XML fallback incidence.
- [`evaluations/legacy-cli-agent-cleanroom-20260714.md`](evaluations/legacy-cli-agent-cleanroom-20260714.md)
  preserves historical pre-canonical raw-XML evidence. It does not validate the
  current Intent Model workflow.

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
