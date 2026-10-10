# Step 92: accept two Runtime source responsibilities

Base: `694c4208`. Astra found misleading leaf descriptions, not evidence for a
physical move. Runtime resolves statement/context inputs; IO reads and selects
rows. Accept only reference.py and variable.py after independent source review.

Spec: `protocol.md`; existing source contract and Astra's source review.

## Global Constraints

- Correct their two module sentences in the mounted Runtime source contract
  and matching `target_module_concerns` in `structure-review.json`.
- Reference: adapt statement and runtime seed state to IO loading/selection.
- Variable: plan execution modes and resolve runtime state into IO operations.
- Keep component owners, interfaces, requires, rules, paths and source unchanged.
- Record the accepted leaves and evidence in one short experiment receipt.
  Other leaves and EE parity remain unaccepted; no new acceptance registry.

## Task 1: independent source QA

Luna QA derives concerns from both sources, callers and IO callees before
   reading a proposed replacement. Challenge placement and edge cases; reuse
   existing tests. Add tests only for a demonstrated missing invariant.

## Task 2: implement the four sentence replacements

Luna independently traces the code before editing; stop if ownership is not
supported. Use the same exact sentence in each declaration and manifest entry:

- reference.py: Resolves reference options and runtime seed state for IO reads and selection, and identifies when rebuilt tasks need shared rotation.
- variable.py: Plans variable source modes and adapts statement and runtime state to IO reads and row selection.

## Task 3: verification, review and checkpoint

Root runs both existing reference-task/source-routing test files and Make
   architecture-definition-check. Compare published 0.8.4 report/validation
   with the base; only target description text may differ, not measured facts.
   No descriptor oracle claim is needed for metadata-only edits.
Astra reviews specification and quality. Root preserves dirty primary work,
   commits/pushes only this slice, keeps PR274 Draft and regenerates the report.

No source/test/descriptor/baseline changes, permission expansion or ArchKeel
implementation. A real checker blocker requires a reproducible issue and stop.
