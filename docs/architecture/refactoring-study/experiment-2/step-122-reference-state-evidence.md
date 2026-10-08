# Step 122 — reference and state-machine ledger join

The immutable 931-path ledger now has **66 reviewed owner profiles** and 865
without one. Only eight reference-distribution and three state-machine rows
change from Step 120; the other 920 rows remain byte-identical. Historical
statuses, input identities, review queues and `c992` parity fields are preserved.
Reviewed profiles do not certify standalone safety or frozen-oracle equivalence.

Nine reference tests passed at each actual `12d5`/`c65` checkpoint. Eight consume
the XML cohort; one checks its manifest. Negative tests accept broad `Exception`
with matching messages, so they do not prove concrete exception classes.

Native preflight established local SQLite with no descriptor/CWD/home profile
overrides in fresh working directories. Setup SQL drops/recreates only their
scratch `items` table; each final database contains four rows. Different native
configuration can redirect that SQL, so general execution safety remains
UNKNOWN. The initial socket-bind startup failure and authorized retry are kept.

The three state-machine rows reference [Step 121](step-121-state-machine-name.md):
16 cases per phase and three equal captures at actual HEAD `296`, with recorded
before/after file hashes. The committed `99d` statement file matches the after
bytes; this does not relabel those runs or certify the original frozen control.

[The receipt](step-122-reference-state-receipt.json) identifies the corrected
ledger, exact delta and independent QA. Full acceptance remains FAIL.

LOCAL VERIFIED: 931 unique paths; exact 11-row delta; unchanged prior evidence;
nine reference cases per checkpoint; reviewed native configuration and inputs.
CI-ONLY VERIFICATION: no dedicated comparison for these supplemental owner runs.
