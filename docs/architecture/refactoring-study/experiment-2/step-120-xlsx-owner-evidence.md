# Step 120 — complete XLSX owner cohort

All 12 XLSX descriptors now have reviewed owner evidence: the nine
missing-workbook inputs and three writers. Exactly **15 existing tests passed
at `12d5e3a5` and 15 at `c65d0090`**, with no skips, failures or errors.

The shared fixture copies descriptors to each test's temporary directory.
Existing tests create their own workbooks there; outputs remain under that
directory. Astra, independent implementation/QA and root reviewed source paths,
configuration, scripts, ownership and effect boundaries before execution.
No services, XML, test, oracle or production code changed.

The project Python environment and standard plugins ran serially, with explicit
clone import roots and development configuration. Independent QA and root
verified exact selected/JUnit node sets, actual commits, input hashes and logs.
The first sandbox attempt stopped before collection; the identical profile then
passed under authorized socket access. Its initial stderr was not retained;
that startup diagnosis is recorded by the execution receipt, not independently
verified from a raw initial log.

## Proof limits

Assertions check selected values, row counts, ordering, paging, transformations
and chunk completeness. Seeded tests replay within each revision; they do not
record exact cross-revision values. The unseeded test checks one permutation.
Invalid-workbook coverage accepts any exception with the expected message.
Complete workbook contents and ZIP bytes are not compared. Workbook handles
are not always explicitly closed; final output retention follows pytest's
temporary-directory lifecycle. This is not an OS sandbox.

## Full ledger

[The receipt](step-120-xlsx-receipt.json) identifies the immutable ledger and
review/run artifacts. Only the 12 XLSX rows change from Step 119; all 43
Authoring rows remain identical. There are **55 mapped owner-evidence paths**
and 876 without a reviewed owner profile. All 931 input paths remain accounted
for; review queues and historical statuses are unchanged.

The nine missing-workbook tags remain: the generic recorder does not create
the native test fixtures. Owner-test success does not upgrade those historical
UNVERIFIED records, replace frozen-oracle proof or relabel `c65` as `c992`.
Original-control and current-checkpoint runtime parity remain unassessed in this
ledger. Full architecture, DSL and report acceptance remains **FAIL**.

LOCAL VERIFIED: independent full-cohort preflight; exact 15-test results per
checkpoint; immutable inputs, run receipts and ledger delta checked.
CI-ONLY VERIFICATION: these supplemental runs have no dedicated CI comparison;
existing experiment CI and its strict architecture failures remain separate.
