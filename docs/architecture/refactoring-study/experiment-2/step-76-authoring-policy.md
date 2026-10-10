# Step 76: Authoring verdict policy

Acceptance and replay policy now live in `authoring/domain`; the four existing
capture records live in `authoring/contracts.py`. Application keeps transaction
sequencing; adapters execute and produce evidence. No new DTO, shim or algorithm.
The local interface publishes eight service-used operations. See [Amendment 80](amendment-80.md).

Independent Luna implementation and QA; root integration; Astra design/review.
Astra found a missing export-list entry and two untested import forms. Both were
corrected and independently rechecked. Function/class bodies and record defaults
match the frozen source; imports, owner paths and export lists change deliberately.

LOCAL VERIFIED: focused execution suite 116 passed; corrected import guard
4 passed. The exact staged checkpoint, excluding older dirty work, passes Make
lint, full-package MyPy (491 files), 1,531 unit tests (11 skipped, 1 xfailed),
5 recursive-definition tests and 4 inner-target tests. The exported checkout
initially lacked Git history; read-only access to the frozen Git objects lets
the unchanged architecture tests pass. The primary index stayed unchanged.

Frozen integration comparison: both inventories contain 930 XML files,
383 CAPTURED, 70 EXPECTED-ERROR, 16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE and
384 UNVERIFIED. All 109 captured seeded digests and four projection payloads
match. The unchanged frozen comparator remains FAIL: 470 incomplete records,
9 unseeded differences and its stale capabilities-version check (480 total).
No new exclusions or descriptor/oracle changes. Copied snapshot Git metadata
is not source provenance; the compared product-file hashes establish the freeze.

Released ArchKeel 0.8.1 (analyzer 0.60.0): 112 violations, 158 counted UNKNOWNs
(233 raw records), 145 typing positions, 2 package-roll-up cycle edges.
Violation and UNKNOWN ID sets are unchanged from Step 75. The unreleased
0.8.2 hierarchy candidate at `5d1506f11` produces byte-identical canonical JSON.
Browser samples show both new policy targets and their responsibility sentences;
Actual retains the physical Domain scope. Diff explicitly falls back to global
categories for an unindexed leaf. Full semantic/report acceptance remains open.

CI-ONLY VERIFICATION: no Step 76 result yet. Step 75 run `36766950609` passes
normal test/build lanes but fails architecture. This checkpoint does not close
the full descriptor gate, authorize a merge/release or claim EE conformance.
