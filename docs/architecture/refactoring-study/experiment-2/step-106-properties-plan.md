# Native Runtime properties typing

> Use superpowers:subagent-driven-development. Root owns integration, docs and
> Git. Independent Luna agents own tests and implementation; Astra reviews.

**Goal:** Replace missing SetupContext property annotations with truthful types.
**Architecture:** Preserve the existing mutable user-keyed dictionary and identity.
**Tech stack:** Project Python 3.11, pytest, Ruff, MyPy; published ArchKeel 0.9.0.
**Spec:** [Amendment 98](amendment-98.md), Astra's delegated source-only decision.
Base `46a3f07f412843d2697503ee143c8b43c26c3c2d`; isolated `ce-registry-084/datamimic`.

## Constraints

- Only constructor/backing/getter/setter property annotations in `context.py`.
- Use `dict[str, object]`; constructor alone also accepts None.
- No runtime statement, caller, RunRequest, parser or generator changes.
- No cast, copy, wrapper, new dependency or runtime validation.
- Freeze contracts, allowances, baseline, budgets, gates and descriptor oracle.
- Existing architecture FAIL remains visible. Annotation disclosure is not PASS.

## Review focus

Native Python integer and nested property values must remain valid. Empty and
nonempty dictionaries retain identity; includes mutate them in place; deepcopy
preserves shared references inside the copy, not references to the original.
RunRequest remains narrower. Full MyPy alone does not prove the unchecked
SetupTask/parser hop is typed end to end.

### Task 1: independent Luna QA

Own only `tests_ce/unit_tests/test_contexts/test_setup_context.py`.

- [ ] Add exact annotation-contract tests that fail before implementation.
- [ ] Reuse the context helper; test None/fresh state, supplied empty/nonempty
  identity, replacement identity, int/nested values, real include merging and
  deepcopy isolation/shared-reference behavior. Avoid duplicate existing checks.
- [ ] Run RED with normal project pytest plugins; do not edit source or contracts.
- [ ] After implementation, independently run GREEN and challenge narrow types,
  copying, setter omission and include behavior. Keep mutations scratch-local.

### Task 2: independent Luna implementation

Own only `datamimic_ce/engine/runtime/contexts/context.py`, after root verifies RED.

- [ ] Annotate constructor, backing field, getter and setter exactly as specified.
- [ ] Preserve executable AST after erasing annotations.
- [ ] Trace callers and run full-package MyPy/Ruff. Invariant-dictionary errors
  stop this slice; do not widen or copy upstream objects to silence them.

### Task 3: root acceptance

- [ ] Run context/include/exporter, unit and architecture tests; definition gate,
  full-package lint/typecheck and executable-cycle check.
- [ ] Generate before/after observations and validation with released 0.9.0.
  Compare all decoded evidence; explain each changed finding/UNKNOWN.
- [ ] Verify descriptor bytes, oracle, source inventory, permissions and executable
  AST are unchanged. Full DSL/service and remote CI remain separate evidence.
- [ ] Independent Astra spec/quality review; concise step report; commit/push only
  the coherent reviewed slice to existing Draft PR274. No merge or force-push.

Namespace initializer removal was rejected: it changes discovery semantics without
a demonstrated benefit and conflicts with EE's current shared-package behavior.
Retain all five markers and their honest assignment findings. Errors ownership and
report acceptance remain stopped at ArchKeel #338 and #335/#336 respectively.
