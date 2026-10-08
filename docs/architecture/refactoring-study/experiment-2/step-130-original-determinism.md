# Step 130 — original/current determinism evidence

The original `a219` owner passed 20 tests; current `e7abf836` passed 21.
The additional unseeded source-shape test remains current-only. Both ran once,
with retries disabled, clone-local imports and unchanged reviewed inputs.
[The receipt](step-130-original-determinism-receipt.json) retains the proof.

Two unchanged recorders captured exactly 16 XMLs per checkpoint. All 11 seeded
result/output digest records match across original-source recapture, current CE
and retained historical `3b844` execution. Historical source identity stays distinct.
Both recaptures used the same current dependency environment.

Five unseeded strict comparisons remain **FAIL**: old records lack presence,
schema and nested evidence. Common recorded field types, counts and output names
match, and native variability assertions pass; neither replaces strict acceptance.
Successful recorder child streams and generated rows were not retained.

Exactly 16 ledger rows gain reviewed owner/capture profiles; the other 915 remain
byte-identical. Reviewed profiles increase **71→87**, leaving **844 UNKNOWN**.
Historical statuses and c992 parity fields remain unchanged. This is not 87
parity passes or a general standalone-descriptor certificate.

Import-gate failures, the pre-collection socket denial and later corrections are
preserved. No failed native assertion was retried. Seeded four-worker requests
are serialized by CE policy; actual multiprocessing and EE remain outside scope.

LOCAL VERIFIED: 20/21 native tests, zero failures/errors/skips; 32 captures;
11 three-way seeded digest equalities; unchanged inputs/source and local cleanup.
CI-ONLY VERIFICATION: exact `e7` PR/push runs each finished with 24 successful
jobs, two architecture failures and two skips. Downloaded eight-cell manifests
pass the unchanged comparator in each run. No CI claim for this later docs commit.

Full acceptance stays **FAIL**: full931 behavior, physical/contracts conformance,
all-depth Actual/Target/Diff navigation and required EE transfer remain open.
