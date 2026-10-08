# Step 25 candidate: rejected DSL facade exports

Astra identified two existing DSL types missing from `dsl.api`:
`TimeSeriesNamespace` and `ConditionBranchStatement`. Independent Luna
implementation and QA passes kept runtime behavior unchanged; 27 focused
branch and time-series tests passed.

The candidate report removed both boundary violations (119 to 117) but grew
UNKNOWN positions from 237 to 238. It exposed an unresolved `datetime` field
inside `TimeSeriesNamespace` and inherited methods on
`ConditionBranchStatement`. The branch-only candidate still grew UNKNOWN
positions to 238. That violates the per-step gate, so both exports and their
new tests were removed. Step 24 (119 violations, 237 UNKNOWN positions) remains
the accepted local state.

This is checker evidence, not permission to drop the two declared types from
the target. ArchKeel [#205](https://github.com/rapiddweller/archkeel/issues/205)
tracks the resolved stdlib `datetime` UNKNOWN; inherited-surface handling is
also still open. Do not count the lower violation total as accepted progress.

LOCAL VERIFIED: the two candidate ArchKeel reports, exact finding-message
diffs, 27 focused tests, Ruff, full-package MyPy, and clean reversal diff.

CI-ONLY VERIFICATION: not run.
