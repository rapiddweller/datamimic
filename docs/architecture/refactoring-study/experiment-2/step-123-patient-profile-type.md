# Step 123 — Patient transaction-profile type

CE's `Patient.transaction_profile` now advertises `Mapping[str, float]` instead
of `dict[str, float]`, matching its existing config and Person getter. Only the
stdlib import and return annotation changed. CE retains the supplied object;
EE explicitly copies it to a dict, so that behavior was not transferred.
Getter introspection intentionally changes; catalogs still advertise `dict`.
That separate metadata mismatch remains open.

**28 existing cases passed before and after** at actual HEAD `99d`. The retained
probe produced identical output for None, string, dict and a non-dict mapping
through real services and cached getters. Identity was checked across both
services; mutation checks covered Person/dict and Patient/custom mapping.
The no-iteration mapping is a getter control, not an enumerable-export contract.
Prefilled-cache `to_dict` checks prove leaf insertion only. Native stdlib JSON
still raises `TypeError` for that mapping; no project exporter was exercised.

The strict two-descriptor comparison remains **FAIL**. It also fails for the
baseline against itself: Patient is UNVERIFIED because nested-list evidence
is incomplete; Person's identical CAPTURED record contains a null field that
the comparator rejects. Patient's unseeded nested cardinalities differ between
runs. Nothing was normalized or resampled. Existing integration assertions
verify seeded cohorts within each phase, not complete cross-phase values.
Patient XML does not request this getter; Person XML reads its None-valued field.
The full inventory and all four projection hashes are unchanged.

Ruff, full MyPy (491 files), formatting, cycle checking and eight definition
tests passed. The fresh pinned report retains 89 violations, 254 canonical
UNKNOWNs, 200 measured UNKNOWN positions and two cycle edges. Violation/module
records match. One Patient API-surface UNKNOWN has a new ID with the same
`class_body_control_flow` reason; none was resolved. The preserved before
packet remains dirty `296`/`a87`; the new packet is dirty `99d`/`fce6663f…`.

[The receipt](step-123-patient-profile-receipt.json) retains source hashes,
controls, captures, strict failures and the UNKNOWN crosswalk. Full acceptance
remains FAIL. No tests, XML, catalogs, contracts, baseline or oracle changed.

LOCAL VERIFIED: bounded before/after owner/probe evidence; package checks;
architecture guards and exact finding delta; independent source/receipt review.
CI-ONLY VERIFICATION: this Patient edit has not yet run in CI.
