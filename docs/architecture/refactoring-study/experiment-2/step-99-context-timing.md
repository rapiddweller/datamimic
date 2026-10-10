# Step 99: unused context timing state

Base `003eb1e7`; published ArchKeel 0.8.5. Astra approved the slice;
independent Luna implementation and QA, root checks and fresh Astra review.

Deleted nine lines: unused `Context._statement_start_times` and its getter/
setter. CE has no callers; generation/export/process timing remains in
`runtime.logging.gen_timer`. No replacement state or API was added.

This removes a public Python member for CE5. External usage is unknown.
EE retains a separate member and an accessor-only test; complete API parity
is not claimed. No EE changes.

## Evidence

- A new two-case test runs real generation and chunked JSON export, with
  reporting enabled and disabled. Both export ids 1, 2, 3 in two chunks;
  only enabled reporting emits generation, export and combined timings.
  It characterizes existing behavior, not a runtime bug fix. Existing
  context/deepcopy checks are reused. Forced reporting-on makes the
  false-mode case fail, proving it catches lost flag propagation.
- Full units: 1,657 passed, 11 skipped, 1 existing xfailed; two existing
  Pydantic serialization warnings. Integration: 567 passed, 2 skipped.
  Functional: 133 passed. API/factory: 393 passed, 1 skipped.
- Ruff and full MyPy pass, 492 production files. Pinned Pylint cycle check,
  7 recursive target checks and 4 physical target checks pass.
- Unchanged `make coverage-unit`: 17,673 of 23,218 executable lines covered
  (76.12%); branch coverage was not collected. This is a current unit-only
  measurement, not a before/after gain or the requested 90% target.
- Fresh decoded observations remove exactly `VIO-8517f06d130af111` and
  `VIO-db2bbc99d9c12043`, with no new semantic findings: 95 → 93 violations.
  142 counted UNKNOWNs and 196 raw UNKNOWN records remain. The runtime
  aggregate loses three decided positions (getter return, setter value,
  setter return); its 22 undecidable positions are identical. Line shifts
  changed 21 otherwise identical finding IDs; comparison uses their full
  semantic content, not IDs alone.

Strict `make architecture-check` remains FAIL, baseline-new 62 and
baseline-resolved 0. The accepted baseline, budgets and gates were not
rewritten. All 492 modules are read and parsed; scanner coverage is unchanged.

The unchanged eight-descriptor replay retains five equivalent captures,
three UNVERIFIED cases and four identical authoring projections. Its strict
comparator remains FAIL on incomplete evidence. Full 930-descriptor parity
and service-backed replay remain open. No descriptor or oracle edits.

LOCAL VERIFIED: checks above. CI-ONLY VERIFICATION: candidate pending push;
no success claimed. Parent CI has an unresolved MongoDB consumer timeout.
Final structure/type closure, EE parity, 90% unit coverage and complete
Actual/Target/Diff navigation remain open; ArchKeel issue #263 tracks the
nested Diff-scope loss. This is a checkpoint, not target or merge acceptance.
