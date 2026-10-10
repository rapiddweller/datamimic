# Amendment 78: weighted CSV return measurement

2026-09-30. Astra approves retaining the correct weighted CSV annotations.
IO still parses arbitrary string headers/cells and selects stored rows with
the injected RNG. No body, interface ownership or descriptor changes.

Under the same public ArchKeel 0.8.1 checker, the IO facade return
`FileUtil.read_csv_having_weight_column` becomes measurable as
`tuple[list[float], list[dict[str, str]]]`:
`UNKNOWN-BOUNDARY-TYPE-POSITION-d8d7b29681956ec7` becomes
`VIO-fa573019a574a357`. Violations change 111 → 112; counted UNKNOWN
positions change 159 → 158. Other finding identities stay unchanged.

This permits only that exact annotation transition, not accepted boundary
debt or a gate pass. Constructor and selector annotations also remain.
Do not grow the baseline/budgets, add an exemption, weaken the oracle or
extend this exception to another position. Step 72 remains gate-red.
Final zero-violation and zero-material-UNKNOWN requirements are unchanged.
Full descriptor/projection parity remains pending and is reported separately.

The open CSV-map boundary needs its own narrow contract decision. A fixed
record DTO would invent constraints on user-defined columns.
