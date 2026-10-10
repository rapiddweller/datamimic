# Step 181 — time-series owner profiles

Ten unchanged native time-series owners ran separately at original `a219163e`
and current source `c2d40e4d`. All 20 exact tests passed. Each owner called
one unchanged fixed-window XML once, and all ten complete typed captures matched
across endpoints. No native exception occurred.

The [receipt](step-181-time-series-owner-profiles-receipt.json) pins
each separate preflight, collection, native stream/JUnit, capture and comparison.
Both detached clones used the same project interpreter and dependency profile,
normal pytest plugins, serial execution, zero reruns and bounded process
groups. Each collection found the same one-item fixture closure. Loaded CE/test
modules came from their own clones. No Python-level service connection or
subprocess was observed. Tracked sources and protected primary files remained
unchanged; no `temp_result_*` remained.

The accepted ledger starts from accepted Step180, changes ten rows and preserves
the other 921 raw lines byte-for-byte. Independent QA passed: **141/931** owner
profiles are reviewed, leaving **790 UNKNOWN**. Historical oracle and
`c992` fields are unchanged.

This establishes only these ten exact native owner profiles in one current
dependency environment. Standalone XML safety, full transient effects,
interrupted cleanup, frozen-oracle parity, other descriptors and EE remain
UNKNOWN.

LOCAL VERIFIED: 20 exact native tests, complete typed capture parity,
identities, dependencies, cleanup and accepted ledger delta.
CI-ONLY VERIFICATION: none for this bounded evidence step.
