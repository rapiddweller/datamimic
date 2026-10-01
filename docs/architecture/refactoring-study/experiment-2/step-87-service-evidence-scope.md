# Step 87: service evidence scope

The descriptor ledger validates every historical evidence row against its class,
reference, and tracked in-repository XML path before partitioning. Live inventory
entries and counts stay limited to current service scope; validated evidence
outside that scope appears in `historical_out_of_scope_entries`.

All statuses describe historical comparisons. `current_parity_status` is
`not-assessed`; no row certifies current-HEAD parity. The revision headers remain
historical control metadata, not a claim that every row used the same execution
pair.

LOCAL VERIFIED on the isolated three-file slice above `e4d233f9`: 1,586 unit
tests pass (11 skips, one existing strict xfail), plus 120 focused ledger/oracle
tests, Ruff and full-package MyPy. The CLI retains 224 live paths and ten
supplemental records. Product code, XML and the oracle/comparator are unchanged.
ArchKeel 0.8.3 still reports FAIL: 106 violations and 157 counted UNKNOWN
positions. This reporting fix does not change that architecture result.
