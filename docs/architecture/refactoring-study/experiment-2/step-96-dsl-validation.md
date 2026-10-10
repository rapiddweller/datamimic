# Step 96: bounded DSL validation acceptance

Local bounded acceptance passes for the raw DSL pre-validation boundary.
Published ArchKeel 0.8.5 compared the actual parent `bd19d370` with the
candidate: violations fell from 103 to 95. Exactly eight intended validator
input/return findings disappeared; no finding was added, and no remaining
finding changed.

All 204 raw UNKNOWN records preserve IDs and semantics; 150 remain counted.
The `constraints.values` generic UNKNOWN has updated source-symbol/evidence
references for its annotation. `baseline_new` changed 67 -> 63;
`baseline_resolved` stayed 0. Baseline, budget and oracle were not edited.
Opaque-value acceptance does not prove type closure, and lazy-supplier UNKNOWN
evidence remains visible. The historical capability digest drift was retained
and accepted by Am60.

Fresh local checks: 123 targeted tests; 1,158 relevant tests passed, 2 skipped;
1,649 unit tests passed, 11 skipped, 1 xfailed; lint passed; MyPy passed on 492
files; recursive definitions passed (7); pinned Pylint passed. Eight frozen
descriptors had 0 differences (four captures, four expected errors), and four
projections matched. The capability projection hash changed across the version
transition; the comparator accepted the recorded drift.

Fresh root reruns passed: 123 targeted tests, lint, MyPy scan of 492/492 files,
and physical-target checks (4 passed).

This is not whole-goal or full-suite acceptance. The runner inventoried 930 XML
descriptors but executed only the frozen eight; full 930-descriptor parity,
unseeded parity, 90% coverage, and CI remain unverified. In the UI sample,
Target runtime/tasks/values/structured opened all four target modules with
English responsibilities; Actual worked at the same physical scope. Diff
shows 95 violations and 204 raw UNKNOWN records but reports no matching scope,
so full UI acceptance is not claimed. PR readiness remains open.

LOCAL VERIFIED: Fresh root reruns and independent QA/review results above.
CI-ONLY VERIFICATION: not run; no CI result claimed.

Evidence files: `.superpowers/sdd/step-96-dsl-validation-plan/qa-report.md`,
`.superpowers/sdd/step-96-dsl-validation-plan/final-review.md`, and
`parent-comparison.json` in the primary checkout's
`test-artifacts/ce-step96-report-ui/`.
