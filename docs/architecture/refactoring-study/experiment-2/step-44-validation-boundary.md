# Step 44: narrow the DSL validation boundary

Moved the five shared checks from `ModelUtil` methods to module functions and
updated all DSL and Authoring callers. Authoring imports them from `dsl.api`;
the class is no longer exported there. [Amendment 66](amendment-66.md) records
the contract correction. No compatibility wrapper or new runtime layer was added.

The local ArchKeel `0.8.1.dev20+g0c1252490` report at
`test-artifacts/architecture/ce-current-step44-209/architecture.report.html`
moved from 123 to 106 violations and from 194 to 189 UNKNOWN positions. DSL
boundary findings moved from 31 to 14. All 490 files still parse; AST coverage
is 100%. The frozen baseline remains red: 84 new positions and zero resolved.
The remaining eight open-map positions are real raw XML inputs; the `Constraint`
alias finding persists despite its exact declaration.

Twelve selected descriptors: nine captured and three expected errors. The five
count-range cases match Step 41 exactly; the three state-machine cases match
Step 43 exactly. Weighted-value positive and negative cases passed independent
QA tests. All four Authoring projections are semantically unchanged; only the
capability package version changed with the commit count, as Amendment 60 permits.

LOCAL VERIFIED: 1,471 unit tests passed (11 skipped, one xfailed); 141 focused
QA tests; nine architecture tests; Ruff, full-package MyPy, Pylint import-cycle
gate, `git diff --check`, targeted descriptor/projection comparison, and local
ArchKeel report/validation.
CI-ONLY VERIFICATION: not run. Full descriptor corpus, external services, EE
alignment, and the remaining boundary findings are open.
