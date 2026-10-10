# Step 99: remove unused context timing state

Base `003eb1e7`, published ArchKeel 0.8.5. Astra approved removing
`Context.statement_start_times` and its backing dictionary: CE has no
callers; generation timing belongs to `runtime.logging.gen_timer`.

This removes a publicly re-exported Python member for CE5. External use
is unknown. EE retains its separate member and an accessor test; record
that alignment difference, without changing EE or adding a replacement.

## Task 1: independent QA

Own only a focused runtime-timing test under `tests_ce/unit_tests/` and
ignored evidence. Production and contracts are read-only. Independently
trace context construction/deepcopy, generate/export timing and reporting
on/off. Reuse existing tests; add only missing checks of real observable
timing/output behavior, not source text or member absence. Establish
the unchanged baseline before implementation. Check the candidate with
the same tests, Make units/lint/full MyPy and relevant lifecycle paths.
Do not change XML, oracle, skips, baselines, budgets or gates. Do not commit.

## Task 2: independent implementation

Own only `datamimic_ce/engine/runtime/contexts/context.py`. Inspect callers
independently. Wait for root's baseline gate, then delete the unused field,
getter and setter. No replacement, unrelated cleanup, test, contract or
EE edits. Do not commit.

## Acceptance

Root compares fresh parent/candidate observations using published 0.8.5.
Remove exactly `VIO-8517f06d130af111` and `VIO-db2bbc99d9c12043`, add no
findings and preserve UNKNOWNs and physical/dependency gates. These
existing failing boundary checks are the pre-change negative evidence.
Compare the same bounded DSL/projection subset; retain all unresolved
oracle cases. Full 930-descriptor parity is not certified by this step.

Astra independently reviews the complete diff and evidence before root
commits/pushes to Draft PR274. Generate accessible HTML/JSON from the
committed checkout. Keep the global goal and final acceptance open.
