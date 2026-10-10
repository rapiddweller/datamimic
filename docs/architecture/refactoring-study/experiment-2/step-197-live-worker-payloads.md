# Step 197 — nonempty live worker payloads

One identical raw XML case ran once at original `a219163e` and current `7e9e8973`.
Current production matches primary `f1308a30`. Each native Pool used two actual
spawn workers, producing six ordered typed rows with identical results.

The parent serialized four callables, including an inline Python helper, and
a generator registry containing a named machine definition and its cached walk.
Exact native byte sidecars match both children's incoming payloads. After native
restoration, the factory reuses the restored cached generator; actual calls emit
`alpha, beta, gamma` per chunk and invoke the restored helper with integer IDs.
Chunk returns, merged output and final capture agree: IDs 1–6 and derived values
17, 27, 37, 47, 57, 67. No warmup, observer invocation, extra deserialization or
RNG replacement was used.

Both runs exit zero without timeout; process groups are gone and leaders reaped.
The producer's offline verifier rejects 48 damaged-evidence controls. The
[receipt](step-197-live-worker-payloads-receipt.json) binds raw proof and review.
Frozen preflight prose named the cache key incorrectly; the observed key is
`rows|status|payloadWalk`. Product inputs and preflight bytes remain unchanged.

This proves this fresh inline helper and finite-cycle machine transfer. Native
serialized bytes differ across revisions; no persisted-pickle, other-generator,
Ray, service, performance or complete DSL compatibility claim follows. No new
CE defect appeared, no production change was made and no corpus row is promoted.

LOCAL VERIFIED: two native executions, actual workers, nonempty payload transfer,
cache reuse, function/generator calls, typed output equality and cleanup.
Independent raw QA confirms the sealed packet and rejects 16 additional coherent
mutations. CI-ONLY VERIFICATION: none for this bounded case.
