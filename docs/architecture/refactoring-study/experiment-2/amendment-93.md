# Amendment 93: dynamic setup state measurement

2026-10-02. Astra, delegated architect, approves retaining this exact Step 101
annotation disclosure as a red checkpoint, not a per-step or final gate PASS.
Namespace/globals carry arbitrary script objects and classes; deepcopy memo
also holds arbitrary objects. DTO/JSON narrowing or wrappers would misstate
the existing contract. No dynamic-map exemption is approved here.

Published ArchKeel 0.8.5: 93 -> 102 violation records (12 added map/object
findings, 3 raw-dict records replaced); counted UNKNOWN 141 -> 134, raw 195 -> 188.
Exactly these seven missing-annotation records disappear:

- `UNKNOWN-BOUNDARY-TYPE-POSITION-2172492fc4cf1b61`: deepcopy memo.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-b832cad208a009fc`: deepcopy return.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-1956232153cd3424`: update_with_stmt return.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-5431d2713729b9c9`: memstore_manager return.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-471d00a97d8c55f4`: namespace getter return.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-fe116b9c43799cff`: namespace setter value.
- `UNKNOWN-BOUNDARY-TYPE-POSITION-9185b338a3823f6e`: namespace setter return.

Runtime's summary changes 107 -> 114/129 decided; missing annotations 11 -> 4.
Baseline-new 62 -> 64/resolved 0 remains FAIL. Context's executable AST and the
physical/import/cycle structure are identical. The only executable addition
is Runtime's existing bool-default policy at `bool(stmt.cyclic)`, independently
tested against real Memstore for None/False/True, windowing and row ownership.

Baseline, budgets, rules, allowances, oracle and all 930 XML files stay frozen.
This is not a general exception or permission to waive map/object debt. Final
zero-violation and zero-material-UNKNOWN requirements stay unchanged. Four
bounded replay captures remain UNVERIFIED; the strict comparator still fails.
Full descriptor/service/EE proof and report acceptance remain open.

Evidence: [Step 101](step-101-setup-state.md), ignored independent task reports
and primary `test-artifacts/step-101-semantic-receipt.json`.
