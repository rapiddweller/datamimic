# Step 172 — literal-array owner profile

Six existing `test_array.py` cases were run at `a219163e` and `c9680c37` with
their original XML and owner tests. One case returned exactly
`{"data":[{"status_codes":["001","002","099"]}]}` at both endpoints. The
other five raised native errors with identical complete type/message/cause/
context graphs and source-bound stages. Physical tracebacks remain separate.

The first original startup failed in pytest configuration because its sandbox
denied a local socket. It collected no selected test and executed no descriptor.
That FAIL remains retained. A separately approved socket-capable attempt then
ran the six original cases once; the current endpoint ran them once. Both
successful runs completed their cleanup and preserved the frozen inputs.

Independent QA accepted the bounded comparison and an additive ledger based on
the effective Step 139 ledger. Exactly six rows changed; the other 925 raw lines
are byte-identical. Of 931 inputs, **125 have reviewed owner profiles and 806
remain UNKNOWN**. The accepted ledger SHA256 is
`caa70f800784107dfcf264abc880edc5926eb5b2ed67991b9ea61a33fde43f62`.
[The receipt](step-172-literal-array-owner-profile-receipt.json) pins the
retained evidence and QA decisions.

This is owner-profile acceptance, not standalone XML safety or frozen-oracle
parity. Historical oracle and `c992` fields remain unchanged. Arbitrary,
script-driven, random and parallel arrays, other inputs and EE remain open.

LOCAL VERIFIED: six exact native cases per endpoint, byte-identical capture,
five complete matching error graphs, independent receipt and ledger review.
CI-ONLY VERIFICATION: none for this bounded evidence step.
