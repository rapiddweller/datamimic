# Step 201 — captured client compatibility

**Verdict:** four bounded original/current pairs have identical ordered outputs,
native types, helper counts and observed aliases. Amendment 199's client-free
parallel transfer remains unimplemented. No general DSL or lifecycle parity follows.

Eight raw XML runs compare original `a219163e533d661bcc7bda0faa5ecc77909ab5aa`
with current `ed95b22dc2bcf84a35d45bd2b13d2f49fe4a6460`. Existing local PostgreSQL
and MongoDB services are reused; each case runs once, with fresh owned resources.
Recipes differ only by resource names. Plain helpers, client defaults and closures
each return integer six for all six rows; source fields retain integer/string types.

| Pair | Original main → chunk PIDs | Current main → chunk PIDs | Default is registered client |
|---|---|---|---|
| PostgreSQL serial | 47986 → main | 48052 → main | True |
| PostgreSQL parallel | 48205 → 48208, 48209 | 48282 → 48286, 48285 | False |
| MongoDB serial | 48364 → main | 48415 → main | True |
| MongoDB parallel | 48486 → 48490, 48489 | 48676 → 48680, 48679 | False |

Each parallel case executes chunks [0,3) and [3,6) in two actual spawn workers.
Within each worker, default and closure share one additional client; namespace
`probe` and its simple alias share another. Serial references all match. Parent
post-deepcopy snapshots already show the split. Object IDs are compared only
within a PID. Rejecting these successful captures or merging their identities
would change observable behavior; neither is accepted as a shortcut.

Original Mongo constructs two wrappers in main (parser and registration), current
constructs one (registration). Output parity does not establish constructor or
complete lifecycle parity. All eight processes exit zero without timeout; groups
are gone, leaders reaped and owned schemas/collections removed with absence checks.
No socket-transfer or complete resource-ownership claim follows.

The shared venv's 100 distributions match. Complete per-revision metadata lists
are separately pinned (100/101, including current source metadata); log/version
and whole-environment equality are not claimed. Eleven producer startup rejection
controls and fourteen independent preflight controls remain separate. No retries,
dependencies, services, production code, target permissions or corpus coverage change.

Evidence receipt SHA256: `f36c87ff1dd205469f42f5e561b785cf14ec78a68dc55941f0044fb36099dbb9`
(141 file pins). Constructor-scope addendum SHA256:
`bf0b24f86085c16fb50656cc0be3b3a3c24a5f0563e1f488c082f15f6c5c4c5b`.
Independent raw QA SHA256:
`ee4d15503954f067e836f4828e004a3cdda5ed711faa40d4f5588f20cc34680d`.
QA verifies 3,326 source pins, 2,502 final import hashes and six damaged-evidence
rejections. Its corrected constructor-count assumption and first offline failure
are retained; neither is a native retry. The final receipt supersedes its pending
manifest status; no broader acceptance follows.

[CE #290](https://github.com/rapiddweller/datamimic/issues/290) records the separate,
pre-existing Mongo count-method stub. Ordinary source counts bypass that method.
[CE #281](https://github.com/rapiddweller/datamimic/issues/281#issuecomment-6098728781)
records the new CI source-read timeout without attributing it to client transfer.

LOCAL VERIFIED: eight selected runs and exact typed pair outputs, process/owned
resource cleanup, frozen file/source pins; Ruff, full-package MyPy (488 files),
and 13 architecture-definition tests pass. Independent raw QA accepts this bounded
evidence; its six rejecting controls are separate from the startup controls.
CI-ONLY VERIFICATION: `ed95b22d` has 48 successes, five failures and five skips.
Four failures are architecture jobs; the PR service job has one Mongo timeout
(163 passed, four skipped), while the same-head push service job passes.
Arbitrary captures, injected clients, includes, sequence/target behavior, Ray and
the remaining DSL corpus require separate verification.
