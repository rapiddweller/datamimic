# Amendment 41: preserve row types through IO selection

Nested-key windowing and reference selection now preserve each caller's row
type in their signatures. Selection behavior and the public `io.api` exports
are unchanged.

ArchKeel candidate 0.8.0 reports 14 → 10 violations, but 71 → 75 UNKNOWN
positions: it classifies each `list[T]` facade parameter/return as `other`.
This is not a clean contract pass. Exact `allowed_positions` currently applies
only to nested DTO fields, so it cannot decide these direct signatures. The
TypeVar classifier needs a tool fix before this step can satisfy the
no-new-UNKNOWN gate; do not baseline the four UNKNOWNs away.

LOCAL VERIFIED: 1973 non-service tests passed (13 skipped), including four new
selector edge tests; Ruff, full Mypy, Pylint import-cycle check, recursive
target checks and independent Luna/Terra review passed. The 930-XML inventory
and status counts are unchanged. Two unseeded descriptors vary as on the
prior step; seeded outputs are unchanged. The frozen capabilities hash still
differs, so the oracle command exits 1.

CI-ONLY VERIFICATION: no remote run.
