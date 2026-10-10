# Truthful capture rows implementation plan

> Use superpowers:subagent-driven-development. Root owns docs, integration and
> Git; independent Luna agents own tests and implementation; Astra reviews.

**Goal:** Describe actual native capture rows and make factory overlay policy explicit.
**Architecture:** IO owns capture storage, Runtime owns its result contract,
and Python adapters forward it. No new layer or alias with no invariant.
**Tech stack:** Project Python 3.11, pytest, Ruff, MyPy; released ArchKeel 0.9.0.
**Spec:** [Amendment 99](amendment-99.md), Astra's approved CE 5.0 decision.
Base `26e01b15b5127044a32db64d0206a9d30a057a4e`; isolated `ce-registry-084/datamimic`.

## Global constraints

- Capture type: `dict[str, list[object]]`; retain existing optionality.
- Preserve actual values, row order/count, identities and both capture streams.
- Factory guard only under `custom_data is not None`, directly before each update.
- Exact error: `TypeError("Factory custom_data requires dictionary rows")`.
- Existing capture/entity/count assertions retain precedence; batch is not atomic.
- No cast, ignore, reflection, copy, wrapper, filter, new dependency or EE edit.
- Freeze contracts, allowances, baseline, budgets, gates, XML and descriptor oracle.
- Architecture/oracle FAIL stays visible; no concurrent build and oracle capture.

## Review focus

No-overlay native objects stay valid; empty overlays still validate. Dictionary
subclass update behavior and errors remain. Mixed batches keep prior mutations.
Explicit TestResultExporter capture still duplicates page/lazy rows. Authoring
sample/smoke evidence must not claim filtered scalar rows were exported.

### Task 1: independent Luna QA

Own only existing `test_python_api/test_runtime_boundary.py` and
`test_exporter/test_export_dispatch_semantics.py` under `tests_ce/unit_tests`.
Consumes real Runtime/IO/Python APIs; produces focused regression proof.

- [ ] Reuse existing helpers/tests; literal real-DSL explicit/no-target controls,
  scalar/mapping/nested text, capture identity/order and factory count precedence.
- [ ] RED: public IO getter, RunResult/RunSession and Python wrapper annotations
  and concrete RuntimeRunSession must expose native rows, not `list[dict]`;
  add no private source-text checks.
- [ ] RED overlay policy: scalar/None/update-capable objects reject with exact
  TypeError; no-overlay identity stays. Include empty overlays, empty/mixed batch,
  dict subclass overrides/errors and nested custom-data aliasing.
  Use the real factory with a substituted session for non-dict and row-subclass
  controls; do not claim these rows are reachable through raw XML. Reuse the
  existing real mapping identity test; keep DSL count-precedence proof separate.
- [ ] GREEN and scratch mutants for wrong row narrowing, copying/deduplication,
  missing guard, truthy-only guard, prevalidation/atomic batch and dict.update bypass.

### Task 2: independent Luna implementation

Own only `engine/io/exporters/diagnostics/test_result_exporter.py`,
`engine/runtime/contracts.py`, `engine/runtime/lifecycle/runner.py`, and
`interfaces/python/{datamimic,data_mimic_test,factory}.py` under `datamimic_ce`.
Consumes the approved existing APIs; produces truthful result signatures.

- [ ] After root verifies RED, annotate storage/getter and propagate native-row
  type across result/session/wrapper surfaces. Constructor returns None.
- [ ] Add only the two specified per-row factory guards; minimal local row
  binding if needed. Preserve every other runtime statement and tuple input.
- [ ] Full-package Make lint/typecheck and focused tests; report actual inferred
  consumer types. Never hide MyPy failures behind import policy or casts.

### Task 3: root acceptance

- [ ] Review exact diff and executable AST: annotations plus approved factory
  checks only. Freeze source inventory/XML/policy/oracle; verify all changed findings.
- [ ] Focused and broader unit/architecture/definition/cycle suites, released
  full report/validation. Unchanged red gates are not acceptance.
- [ ] Freeze package metadata during serial before/after capture; distinguish
  current-slice proof, original Step0 proof, expected errors and unresolved cases.
- [ ] Fresh independent Astra review, concise compatibility/evidence report,
  coherent commit/push to existing PR274 only. No merge or force-push.
