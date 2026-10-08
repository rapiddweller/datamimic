# Step 71: correct property-map boundary positions

Added exact `dict[str, str]` return allowances for the DSL parser and the two
IO facade methods. The 0.8.1 before report contained their direct-return
findings (`VIO-64d062f2e6d212ad`, `VIO-1f48d8a90686e874`,
`VIO-47d672b8d0886a2a`). Afterward, all three disappeared; no other violation
or UNKNOWN identity changed. Violations changed 114 to 111; counted UNKNOWN
positions stayed at 159 (234 raw UNKNOWN evidence records in each report). The
Python source digest stayed `787567dc668fcb1210503ae2080c7834216948c56247a144a76ed4f802247caf`.

Four retained independent 0.8.1 checker probes each mutate only the DSL
allowance. A wrong qualified name, parameter position, widened
`dict[str, object]` annotation, or nonempty `properties` field path restores
`VIO-64d062f2e6d212ad`; each report has 112 violations while both IO positions
remain allowed. The source digest is unchanged. No other violation or UNKNOWN
identity changed in the positive before/after reports.

LOCAL VERIFIED: `make architecture-definition-check` passed (5 tests). Root
reported 21 properties and recursive tests passed, Ruff passed and full-package
MyPy passed (491 modules). Strict `make architecture-check` passed cycle,
definition and inner-target gates; final validation remains red with 111
violations, 159 UNKNOWN positions and 73 findings new to the existing baseline.
The existing `typing_positions` budget remains exceeded at 145 against 143;
this slice does not change that measurement or other baseline debt.

CI-ONLY VERIFICATION: not run for this CE slice.
