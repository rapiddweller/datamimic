# Step 128 — one factory failure, one execution error log

Factory `create()` and `create_batch(2)` logged a missing entity twice: once
in `_validate_xml_model()`, then in `execute()`'s catch. Two independent native
probes confirmed it. The fix deletes only the inner log expression, under
[Amendment163](amendment-163-factory-error-log-ownership.md).
[The receipt](step-128-factory-error-receipt.json) retains exact inputs, raw
probes, test failures, successful controls and pinned architecture packets.

The public-path regression failed on unchanged production code because it saw
two ERROR records. Afterward both APIs emit only the existing outer ERROR.
`ValueError` class, args, text and cause/context remain unchanged. Constructor
logging, outer catch/rethrow, lookup, warnings and successful factory mutations
remain intact. Direct private validation no longer logs this failure.

LOCAL VERIFIED: 91 relevant cases passed; after test-style corrections, all six
factory cases and changed-file Ruff/format passed. Full-package Ruff/MyPy passed
for 491 files. Cycle checks, eight definition tests and four inner-target tests
passed. Initial style failures remain in the receipts; final line wrapping has
an identical test AST to the separately verified baseline failure.

Pinned architecture acceptance remains **FAIL**: 89 violations, 254 canonical
UNKNOWNs and 200 measured UNKNOWN positions. Module and violation arrays are
identical before/after. One dynamic-call UNKNOWN record changes because the
deleted unresolved call reduces 1231→1230; no UNKNOWN is resolved or waived.
Packets retain actual dirty HEAD `03bd23d9` and their distinct source digests.

Probe observers count LogRecords; QA's observer suppresses emission, so it
does not prove native stderr routing. An edited early QA JSON is retained as a
derived receipt; the labeled v2 rerun preserves untouched raw output. Earlier
wording about an empty exception string or deletion inside `execute()` is
corrected by the native evidence and exact validation-method diff.

The temporary empty descriptor adds no inventory row. No generated dataset,
full persisted target state or original `a219` runtime parity is certified.
Full architecture and transfer acceptance remain open. CI-ONLY VERIFICATION:
none yet for this source correction.
