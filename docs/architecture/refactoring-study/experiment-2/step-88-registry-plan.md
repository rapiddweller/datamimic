# Step 88: released checker and exact Registry ownership

Spec: `protocol.md`; existing task contract and initializer responsibility.
Baseline: `134628a7d8f0f4355f1c2d3007d5251efdd14ee5`.

## Global Constraints

- ArchKeel is the published `archkeel==0.8.4`, not an editable candidate.
- Only the executable `datamimic_ce.engine.runtime.tasks` initializer gains Registry ownership.
- All existing task owners, public interfaces, requirements and rules stay unchanged.
- No production Python, descriptor, oracle, baseline or gate weakening.
- Independent implementation and QA; Astra decides the boundary. Root owns final staging and commits.
- Preserve the primary checkout's unrelated dirty work. CE PR274 remains Draft.

## Task 1: implement the exact contract migration

Read the existing package initializer, registry and dispatch callers first.
Change `ARCHKEEL_SOURCE` in `Makefile` from `archkeel==0.8.3` to `archkeel==0.8.4`.
Run the new static Registry contract assertion from the existing
`architecture-definition-check` target, selecting only that test (no runtime dependencies).
Add `exact_modules: ["datamimic_ce.engine.runtime.tasks"]` to TASKS-REGISTRY in
`docs/architecture/inner/runtime/tasks/architecture-contract.json`.
Do not broaden its existing `packages` selector or edit any other contract field.
Wait for independent QA's RED evidence before applying these changes.
Run the relevant definition and entrypoint checks; no commit or push by the worker.

## Task 2: independently verify ownership and entrypoints

Own only `tests_ce/architecture/test_registry_entrypoints.py` and QA scratch evidence.
Add one focused assertion to the existing suite for the exact initializer selector
and unchanged Registry package selector; show it fails before implementation.
Reuse the existing cold CLI, fallback/custom registration and multiprocessing checks.
Observe committed baseline and amended contract with the same official package.
Compare all task identities: exactly the initializer changes unassigned to Registry;
all other owners stay fixed. A synthetic sibling must stay outside Registry.
Check TASKS assignment/complete-requires receipts and retain all remaining FAIL/UNKNOWN.
No test-local resolver, fixture framework, source mutation or baseline acceptance.

## Task 3: review, checkpoint and regenerate report

Astra reviews task semantics, code quality and positive/negative evidence independently.
Root checks source/contract digests, changed-file scope and the official checker identity.
Record measured results in `step-88-registry-ownership.md`, then stage only this step.
Commit and push to `experiment/target-architecture-v2`; no CE merge.
Regenerate HTML/JSON with the default published checker. Report open FAIL/UNKNOWN honestly.
Continue with the already approved smoke-export wrapper-removal slice afterwards.
