# Step 126 — Memstore owner evidence

Six existing tests passed at each actual checkpoint, `12d5` and `b0cef82`,
covering five committed XMLs and one temporary raw-getter descriptor.
[The receipt](step-126-memstore-owner-receipt.json) retains the independent
preflights, exact inputs, native execution logs, JUnit and ledger delta.
No source, descriptor, configuration or oracle changed.

The assertions cover CSV iteration, lenient aggregation, namespace binding,
sum→dynamic-count consistency, SQLite filtering to `[1,3]`, and raw script
access. All six tests are unseeded; these are owner assertions, not exact
cross-run dataset comparisons or original `a219` runtime parity.

Both reviews caught the initial profile assumption: the tracked development
profile overrides the XML database path. Astra approved that unchanged,
identical SQLite profile after fresh disposable clones passed import, input
and path checks. HOME stayed unchanged. Capture still writes JSON; native
cleanup removes the database and fixture output/db. Complete persisted target
state was not read back. Post-run cleanup passed; pytest's native `current`
symlink remains contained inside its dedicated temporary directory.

Exactly five existing ledger rows changed; the other 926 remain byte-identical.
Owner profiles increased **66→71**, leaving **860 UNKNOWN**. Historical
statuses, identities, queues and c992 parity fields remain unchanged, including
the filtering descriptor's historical UNVERIFIED status. The temporary
descriptor adds no inventory row. Neighboring large/process cohorts remain
outside this proof.

Full acceptance remains **FAIL**: the architecture, report-navigation, transfer
and full DSL obligations in [Step 125](step-125-boundary-review-decision.md)
remain open. Next is the bounded runtime error/logging transfer audit.

LOCAL VERIFIED: six tests per checkpoint, zero failures/errors/skips; unchanged
13 inputs and native source hashes; clone containment, native cleanup and exact
five-row ledger delta. No product change requires another broad suite.
CI-ONLY VERIFICATION: both `b0cef82` runs completed with 24 successful jobs,
two architecture failures and two skips each. No CI claim for this later
documentation checkpoint.
