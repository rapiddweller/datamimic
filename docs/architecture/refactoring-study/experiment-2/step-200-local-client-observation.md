# Step 200 — local client ownership observation

**Verdict:** selected outputs PASS; Amendment 199's client-free parallel transfer
is not implemented. Current-only observations do not establish original/current parity.

Four raw XML executions at `b8e7342f429b465dae861c79a86311fdb636a23d`
reuse local PostgreSQL 18.6 and MongoDB 7.0.12. Each runs once and returns six
ordered rows with native integer `source_id` and string `label`. No source,
dependency or service replacement occurs.

| Case | Main PID | Actual chunk executors |
|---|---:|---|
| PostgreSQL serial | 42182 | main: [0,6) |
| PostgreSQL parallel | 42270 | 42282: [0,3), 42283: [3,6) |
| MongoDB serial | 42324 | main: [0,6) |
| MongoDB parallel | 42358 | 42361: [0,3), 42360: [3,6) |

Both parallel cases bind actual chunk calls to two Pool members using spawn.
Main constructs the client wrapper, then Context copies and dispatches it with
its namespace alias. Workers restore and use wrappers without calling their
constructors. This confirms [CE #289](https://github.com/rapiddweller/datamimic/issues/289),
not an additional DSL defect. Main serial execution is valid under Amendment 199.

PostgreSQL copy/send snapshots contain no engine; each worker's repeated engine
lookup returns one local engine identity. MongoDB driver construction and close
calls pair within each PID. Neither wrapper transport nor missing explicit
PostgreSQL disposal proves socket transfer or a leak.

All four runs exit zero without timeout; owned process groups are gone and
leaders reaped. Only their fresh schemas/collections are removed; absence is
verified. Nine offline damaged-output/PID/ownership/cleanup controls reject.
Earlier sandbox/environment failures are retained as zero product entries.

Raw packet: `/tmp/ce-step200-worker-lifecycle-20261010/receipt-v3.json`,
SHA256 `8cbe1f04a1086f3b3b97b6cbf6582143e1e99c1d96c6a51a931062c57f588c46`.
It pins 102 files; production tree is `e8ab401f8722e019989165927e1ed66d23643b13`.
Independent raw QA: `/tmp/ce-step200-raw-independent-qa-20261010/qa-review.md`,
SHA256 `60c6d3843a705d7a2bac3535e28dca8ae07177c7699b86762905c808be4bff39`.
Both root and QA verify the raw pins and unchanged production source.

LOCAL VERIFIED: four native cases, observed PIDs/aliases/outputs and owned cleanup.
CI-ONLY VERIFICATION: `b8e7342f` completes with 50 successes, four architecture
failures and four skips; both service jobs pass. Ownership acceptance does not follow.
Ray, custom captures, database targets, includes and sequence behavior remain
outside these four cases. The full refactoring experiment remains incomplete.
