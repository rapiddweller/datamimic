# Step 178 — ID-alias owner profile

The unchanged native `test_id_equals_key` owner ran once at original `a219163e`
and current `16b8e125`. Both passed and returned the same complete typed five-row
capture: `via_id` and `via_key` are string `"42"`, while `seq` is the integer
sequence 1–5. No native exception occurred.

The XML blob is identical at both endpoints. The owner body is unchanged apart
from its moved `DataMimicTest` import. Separate detached clones, the same project
interpreter and dependency versions, normal pytest plugins, serial execution,
zero reruns, and bounded owned process groups were used. Collection found the
same single test and fixture closure. Loaded CE/test modules came from their own
clones. No service connection or subprocess was observed. Tracked sources and
protected primary files remained unchanged; no `temp_result_*` remained.

The [receipt](step-178-id-alias-owner-profile-receipt.json) pins the
preflight, native streams/JUnit, complete captures and comparison. The accepted
ledger starts from accepted Step 176, changes one row and preserves the other
930 raw lines byte-for-byte. Independent QA passed: **128/931** owner profiles
are reviewed, leaving **803 UNKNOWN**. Historical oracle and `c992` fields are
unchanged.

This proves only this exact native owner profile in one current dependency
environment. Standalone XML safety, full transient effects, interrupted cleanup,
frozen-oracle parity, other descriptors and EE remain UNKNOWN.

LOCAL VERIFIED: one exact native test per endpoint, complete typed capture,
identities, dependencies, cleanup and accepted ledger delta.
CI-ONLY VERIFICATION: none for this bounded evidence step.
