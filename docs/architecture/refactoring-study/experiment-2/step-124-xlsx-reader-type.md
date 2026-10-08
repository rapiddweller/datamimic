# Step 124 — XLSX reader return type

`FileUtil.read_xlsx_to_dict_list` now declares `list[dict[str, object]]` instead
of bare `list[dict]`. The existing body stringifies nonblank headers and retains
native cell values, including None. Only the return annotation changed;
consumers, `GenerateFileSource`, errors and workbook lifecycle are untouched.
Return-annotation introspection intentionally changes.

**15 existing owner cases passed before and after** at actual dirty HEAD `99d`.
The reviewed fixture creates its inputs under each test's temporary directory.
This reuses Step 120's 12-descriptor profile, not standalone execution against
missing workbooks. Its assertions cover selected values/order/counts, seeded
replay within each phase, paging, transformation and chunk completeness.

The same immutable two-row workbook produced identical output, preserving
bool/int/float/datetime/time/timedelta/text/None, dropped blank headers and None
padding. Independent mirror controls retain last-write-wins header collisions
and missing-sheet/invalid-ZIP ValueErrors. These are bounded openpyxl 3.1.5
checks, not full exporter or arbitrary-provider proof. All four unchanged
recorder projections match; the frozen capability expectation still differs.

Ruff and MyPy (491 files), cycle checking and eight definition tests passed.
Formatting returns 1 for the same pre-existing unrelated CSV signature in both
baseline and candidate; that signature was left unchanged. The fresh pinned
report retains 89 violations, 254 canonical UNKNOWNs, 200 measured UNKNOWN
positions and two cycle edges. Full finding/module arrays match the retained
pre-XLSX packet. Both packets record actual dirty HEAD `99d`; source digest
changes from `fce6663f…` to `0a38fc3b…`.

[The receipt](step-124-xlsx-reader-receipt.json) retains inputs, exact commands,
check returns, projections and independent reviews. Full acceptance remains FAIL.

LOCAL VERIFIED: 15/15 cases per phase, immutable native-cell control, static
and architecture checks; pre-existing format failure retained.
CI-ONLY VERIFICATION: this combined Patient/XLSX source has not yet run in CI.
