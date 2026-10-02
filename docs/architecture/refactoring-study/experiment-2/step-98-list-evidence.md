# Step 98: list behavior evidence

Base `3d3928bc`. Tests only; published ArchKeel 0.8.5. Independent Luna
implementation and QA, root verification, Astra bounded acceptance.

## Before / after

Both list integration tests previously checked only that execution finished.
An isolated negative control replaced generated lists with `[]`; both tests
still passed. They now capture real results and check item order, exact fields,
fixed values, nested counts and generated value types. Neither XML changed.

Three unit tests use real models, contexts and task dispatch. They check field
isolation, heterogeneous item order, false conditions retaining `None`,
whole-list conversion and preservation of empty collections. No test framework
or production helper was added.

## Verification

- The actual integration test methods reject six corrupted captures: wrong
  count/order, missing field, sibling field leakage, wrong pet count and wrong
  integer-array length. Real positive captures retain two-worker execution.
- Focused root regression run: 8 passed, including unchanged converter and
  memstore assertions. Full units: 1,655 passed, 11 skipped, 1 existing xfailed.
- Ruff and full MyPy: pass, 492 production files. Recursive target checks:
  7 passed; physical target checks: 4 passed; pinned Pylint cycle check: pass.
- Focused statement-plus-branch coverage for ListTask/ItemTask: 32% → 87%.
  Same two existing unit files before/after, plus the three new unit tests.
  This is not repository-wide coverage or proof of the 90% unit-coverage goal.
- Architecture observation is exactly unchanged: 95 violations, 142 counted
  UNKNOWNs, 492 modules. Strict `make architecture-check` remains FAIL;
  baseline-new 63, baseline-resolved 0.

No production, descriptor, oracle, contract, baseline, budget or gate edits.
The same eight-case replay subset retains five equivalent captures and three
UNVERIFIED cases; four authoring projections are identical. Its strict
comparator still fails on those three incomplete-evidence cases. Full
930-descriptor equivalence remains open; the new assertions do not replace it.

LOCAL VERIFIED: tests, negative controls, focused coverage and checks above.
CI-ONLY VERIFICATION: candidate CI not yet verified. Parent `3d3928bc` CI
failed architecture and one MongoDB consumer test with a server-selection
timeout; its root cause remains unresolved. No CI success or merge approval.
