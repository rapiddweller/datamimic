# Step 100: empty echo diagnostics

Base `008d4ce2`; published ArchKeel 0.8.5. Independent Luna implementation
and QA followed Astra's decision in [Amendment 92](amendment-92.md).

The relocated Echo task now accepts absent XML text and continues after an
empty debug message. The statement's optional text and task's `None` result
are declared. Nonempty code, ownership and all 930 XML files stay unchanged.
Empty echo changes deliberately from TypeError to continuation; this is
upstream alignment, not a claim that every old outcome remains identical.

LOCAL VERIFIED: independent QA and root both observed the original two empty
cases fail before the guard; whitespace/interpolation already passed. Normal
plugin-enabled Echo suites now pass 9 tests, including literal single/double
quotes and existing failed-placeholder continuation. The implementer's
plugin-disabled run is not acceptance evidence; root and QA reran normally.
QA: 1,657 units passed, 11 skipped, one existing xfail; two existing Pydantic
warnings remain. Root: integration 571 passed/2 skipped, functional 133 passed,
API/factory 393 passed/1 skipped. Ruff and full MyPy (492 files) pass.
Independent Astra review: spec and code-quality PASS for this bounded step;
the full diff and decoded semantic deltas were reviewed, not just counts.

Semantic comparison: 93 violations unchanged, none added or removed.
Exactly EchoStatement.value's missing annotation disappears: counted UNKNOWN
142 -> 141, raw records 196 -> 195. DSL positions stay 364; decided 309 -> 310,
undecided 55 -> 54. Imports, cycles, packages and modules are identical. The
new debug call is resolved; scanner coverage stays 492/492 files.

Pinned Pylint, seven recursive-definition and four physical-target tests pass.
The unchanged strict architecture gate remains FAIL: baseline-new 62,
resolved 0. No baseline, allowance, budget or gate changed.

Thirteen bounded descriptors were executed before/after: nine have sufficient
unchanged capture evidence. Four nested-list cases remain UNVERIFIED, including
scripted_echo.xml. The strict comparator rejects that incomplete evidence;
it was not changed. Inventory and all four Authoring projections are identical.
Full 930-descriptor/service parity, EE alignment, 90% coverage and all-depth
report acceptance remain open. Nested Diff is tracked by ArchKeel #263.

CI-ONLY VERIFICATION: no candidate CI result claimed before commit/push.
Evidence: the plan's ignored SDD QA/implementation reports and primary
`test-artifacts/step-100-*` observations, semantic receipt and command logs.
