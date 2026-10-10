# Step 193 — real stdlib worker profiles

Original `a219163e` and current `7e9e8973` ran the same three unchanged current
lifecycle owner bodies once each: buffered JSON (5 rows, chunks of 2), lazy
capture (5 rows), and ordered Memstore producer/readback (5 rows). Only the
documented moved DataMimicTest import differs. These are shared native owner-body
profiles, not pytest/plugin runs; the original lifecycle test file is absent.
The failed post-run source-inspection probe is retained separately.

All six runs passed. Passive `sys.setprofile` events show eight actual stdlib
Pool.map executions, each with two distinct spawned workers executing chunks
`[0,3)` and `[3,5)`: 16 worker PIDs in total. Pool process lists, child PIDs,
parent PIDs, native entry/return code paths, and spawn start methods agree.
No worker, method, descriptor, seed or product behavior was replaced.

Lazy and Memstore captures match as ordered, fully typed rows. Three buffered
JSON artifacts match by exact named bytes and by content multiset; filenames,
bytes, parsed rows and both native collision WARNs remain in the raw evidence.
Eight negative controls reject fake main-PID worker evidence, missing/duplicated
rows, and reordered captures. All process groups are gone and leaders reaped;
no timeout, product failure, clone edit or lingering exporter chunk was observed.

Live context/statement/result Pool IPC and empty callable/generator-registry
dill rehydration are evidenced. Both serialized registries are empty dictionaries;
the Memstore context namespace contains `mem`. Nonempty callable or generator
transfer, persisted-pickle compatibility, other start methods/platforms, Ray,
DB/services, interrupted cleanup and complete transient effects remain unproved.
Passive profiling changes timing; this is no performance benchmark. No corpus
ledger row, oracle or baseline is promoted by these generated-fixture profiles.

LOCAL VERIFIED: six shared owner-body runs, real worker PID/start-method/chunk
evidence, ordered typed results, exact JSON bytes, eight negative controls,
matching dependency/environment profiles, source bindings and bounded cleanup.
CI-ONLY VERIFICATION: none for these native profiles. The probe changed no
production, clone source or ledger. The [receipt](step-193-real-workers-receipt.json)
binds the immutable raw captures and independent QA.
