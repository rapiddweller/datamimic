# Step 185 — seeded native owner profiles

Eight exact native owners were compared at original `a219163e` and current
source `5c218f8f`: seeded Hash, two time-series comparisons, four seeded local
source reads and finite unique values. They cover ten new XML rows. All 16
native tests passed; all 34 ordered typed captures and type trees matched.
Stable log messages and stdout matched, including the single identical
low-page-size WARN in the pagination owner.

The [receipt](step-185-seeded-owner-profiles-receipt.json) pins
unchanged owner/XML/fixture inputs, exact collections and native runs,
complete captures, streams, dependencies, side-effect observations and cleanup.
The project venv, normal plugins, serial execution and bounded process groups
were used. The rerun plugin needed a socket-capable host for collection. An
initial host-global-Python preflight was excluded before collection; one
default-sandbox collection failed on localhost bind and remains a separate
FAIL receipt. Every selected native owner then collected and ran once per
endpoint under the same socket-capable condition.

The accepted ledger changes ten previously UNKNOWN rows and preserves 921
other raw lines byte-for-byte. Independent QA passed: **166/931 reviewed** and
**765 UNKNOWN**. Historical oracle, `c992`, and
comparator fields are unchanged. One already reviewed base time-series XML
participated in an exact owner comparison but its ledger row did not change.

Acceptance uses the independent raw-log comparison, preserving severity,
logger, task, product names, counts and message structure. Only timestamps,
PID, task IDs, clone paths, elapsed seconds and throughput are normalized.
The producer's whole timing-message masking is insufficient alone and must
not be reused as semantic log proof. Full-log byte equality is not claimed.

This is exact native owner-profile evidence in one dependency environment.
Standalone XML safety, complete transient effects, interrupted cleanup,
frozen-oracle parity, other descriptors and EE remain UNKNOWN.

LOCAL VERIFIED: 16 exact native tests, 17 typed capture pairs, stable
output/diagnostics, identities, dependencies, side effects, cleanup and ten-row
ledger delta.
CI-ONLY VERIFICATION: none for this bounded evidence step.
