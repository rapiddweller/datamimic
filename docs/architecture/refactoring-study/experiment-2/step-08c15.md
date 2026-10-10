# Step 08C15: finish Authoring and Resources typing

## Change

- Removed the remaining Authoring and shipped-resource `Any` and unchecked type escapes.
- Replaced the untyped constraint-renderer table with explicit typed dispatch.
- Routed packaged-demo discovery through the new typed `resources.api` facade.
- Replaced a demo's private `BankAccount` field access with a public read-only property.

## Evidence

- ArchKeel violations: 234 -> 202; 30 baseline fingerprints resolved and 0 added.
- NO-MAGIC findings: 231 -> 199; none remain in Authoring or Resources.
- `calls_unresolved`: 1,399 -> 1,397; typed positions: 390 -> 350; private crossings remain 0.
- Authoring, MCP, and CLI gate: 498 passed. Final reference/schema/API/CLI regression set:
  103 passed. Finance demo integration: 1 passed.
- Descriptor oracle against frozen Step 0: 930 compared, 0 differences, and 0 optional-shape
  variances. Counts remain 454 captured, 62 expected-error, 16 non-descriptor, 76 unrunnable,
  and 322 unverified; all four projection hashes are unchanged.
- Full-package Ruff passes. Full-package mypy still reports only the two optional Ray imports owned
  by the parallel Runtime lane.

One first oracle run lost the child result for `variable_entity/test_city_entity.xml` with exit 0.
The isolated case and a second complete oracle run both matched Step 0, so this is recorded as
runner result loss rather than a behavior change.
