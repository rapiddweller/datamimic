# Step 64: finish DSL accessor typing

`GenerateStatement`, `ReferenceStatement`, `NestedKeyStatement`, and
`VariableStatement` now annotate existing model-backed accessors. `dsl.api`
publishes the existing `ReferenceField` type. The nested-key task passes its
already-checked script to the evaluator instead of rereading it.
No descriptor or model schema changed.

LOCAL VERIFIED: 82 focused DSL, reference, distribution, and nested-key tests;
Ruff and full-package MyPy (491 files). Two seeded descriptor captures match
Step 0 exactly. Two invalid reference descriptors preserve their error text,
but remain `UNRUNNABLE` under the comparator. One unseeded nested-key case is
`UNVERIFIED`; valid DB-backed references and the full 930-descriptor inventory
are not yet equivalence-proven. The Step 63 candidate report remains FAIL:
115 violations and 161 UNKNOWN positions, with 491/491 modules parsed.

CI-ONLY VERIFICATION: not run.
