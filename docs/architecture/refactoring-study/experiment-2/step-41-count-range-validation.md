# Step 41: Compare count ranges numerically

CE compared raw XML `minCount` and `maxCount` strings before Pydantic parsed their
integer fields. Thus `9..10` failed and `10..9` could pass. EE already compares
numbers. The shared CE validator now uses Pydantic's integer parser for the
comparison; malformed bounds without a count conflict still receive normal
field-validation errors.
Both `<generate>` and `<nestedKey>` use this validator. No contract, descriptor,
module ownership or public API signature changed.

Independent QA added 14 model tests covering both callers, reversed and malformed
bounds, count exclusivity, integral decimal strings and infinity. Reviewer found
the decimal-string bypass in the first `int()` implementation; the final parser
handles the same values as the model fields. The 4 existing count-range
integration tests pass.

The five affected descriptors match the previous CE capture exactly: four
captured result/output digests and one expected error. All four authoring
projection hashes match the previous CE capture; the capability hash still
differs from frozen Step 0 under Amendment 60. The current ArchKeel report has
the same 123 violation messages and 194 UNKNOWN IDs as before this step.
Its exact violation IDs shift with source line numbers; the baseline gate remains
red at 93 new findings and is **not** claimed to pass.

LOCAL VERIFIED: 18 focused model/integration tests; 1,458 unit tests passed,
11 skipped, 1 xfailed; 9 architecture-definition tests; `make lint typecheck`;
`git diff --check`; targeted descriptor and projection comparison.
CI-ONLY VERIFICATION: not run. External-service, full descriptor and EE runtime
gates were not rerun for this slice.
