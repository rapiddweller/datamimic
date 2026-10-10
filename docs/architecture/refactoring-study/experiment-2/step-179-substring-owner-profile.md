# Step 179 — Substring owner profile

The unchanged native `test_substring_slices_like_python` owner ran once at
original `a219163e` and current `1e7d97df`. Both passed and returned the same
complete typed capture: one string row with `full=0049-171-2635861`,
`last4=5861`, `area=171` and `from2=49-171-2635861`. No native exception
occurred.

The XML blob is identical at both endpoints. The owner body is unchanged apart
from its moved `DataMimicTest` import. Separate detached clones, one project
interpreter and dependency profile, normal pytest plugins, serial execution,
zero reruns and bounded owned process groups were used. Collection found the
same single test and fixture closure. Loaded CE/test modules came from their
own clones. No service connection or subprocess was observed. Tracked sources
and protected primary files remained unchanged; no `temp_result_*` remained.

The [receipt](step-179-substring-owner-profile-receipt.json) pins preflight,
native streams/JUnit, complete captures and comparison. The accepted ledger
starts from accepted Step 178, changes one row and preserves the other 930 raw
lines byte-for-byte. Independent QA passed: **129/931** owner profiles are
reviewed, leaving **802 UNKNOWN**. Historical oracle and `c992` fields are
unchanged.

This establishes only the exact native owner profile in one current dependency
environment. Standalone XML safety, full transient effects, interrupted cleanup,
frozen-oracle parity, other descriptors and EE remain UNKNOWN.

LOCAL VERIFIED: one exact native test per endpoint, complete typed capture,
identities, dependencies, cleanup and accepted ledger delta.
CI-ONLY VERIFICATION: none for this bounded evidence step.
