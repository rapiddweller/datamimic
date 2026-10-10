# Step 196 — conditional inline keys lose uniqueness

Three current-only raw XML cases ran once against `7e9e8973`; production
matches `a939a929`. Each requests 16 rows from 16 integer values with
`unique="true"`. No seed, retry, distribution override or source change was used.

| Placement | Requested / selected workers | Rows / distinct codes |
|---|---|---|
| Direct key | 2 / 1, no Pool | 16 / 16 |
| condition/if key | 2 / 2, two real spawn workers | 16 / 9 |
| Same conditional key | 1 / 1, no Pool | 16 / 9 |

Row IDs, integer types and row order remain intact. Serial duplicates rule out
an explanation based only on parallel eligibility. Per-row branch task creation
resetting the task-owned iterator is a source-supported hypothesis; iterator
identity was not instrumented. Exact random draws are not replay guarantees.

After deduplication, the independently checked inline-key case extends
[CE #282](https://github.com/rapiddweller/datamimic/issues/282#issuecomment-6097790836),
which already covers conditional unique references. The issue now names keys
and references and includes XML, direct/serial controls and source links.
The [receipt](step-196-conditional-unique-keys-receipt.json) binds raw evidence,
independent QA and exact issue readback. No duplicate issue or behavior fix.

LOCAL VERIFIED: three native cases, parsed plans, typed rows, actual workers,
19 producer and six independent rejecting controls, two positive controls and
scoped cleanup. CI-ONLY VERIFICATION: this case has no CI coverage or fix.
Historical behavior, regression attribution, key exhaustion, variables, other
branches/backends and whole DSL parity remain unproved; no ledger promotion.
