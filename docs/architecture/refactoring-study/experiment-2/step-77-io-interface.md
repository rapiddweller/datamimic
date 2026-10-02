# Step 77: IO interface ownership

Implemented and locally reviewed. Eight root aliases leave the Runtime-facing IO facade; existing
owners and reader/cache identity stay unchanged. Independent Luna QA and
implementation; Astra design/review; root contracts, integration and Git.

The documented FileUtil root import deliberately breaks for CE 5.0, not 4.x.
Use `datamimic_ce.engine.io.files.api.FileUtil` instead. External consumers
are UNKNOWN. See [Amendment 81](amendment-81.md), which supersedes historical D4.

No descriptor, algorithm, baseline, budget or oracle changes. Dropping duplicate
FileUtil findings is surface contraction, not repaired reader types. The public
file interface's boundary-type coverage gap remains open.

LOCAL VERIFIED (dirty integration): real QA RED `5 failed, 10 passed`; GREEN
113 focused tests, 53 boundary/DbUnit/FCW/exporter/source tests, full unit suite
`1540 passed, 11 skipped, 1 xfailed` (two existing serializer warnings).
Ruff, MyPy (491 files), five target-definition tests, four inner-target tests
and pinned Pylint executable-cycle check pass.

Exact clean checkpoint (HEAD plus only Step 77): Ruff, MyPy (491 files),
`1531 passed, 11 skipped, 1 xfailed` (same two warnings), 51 affected boundary/
descriptor roundtrips, five target-definition tests, four inner-target tests
and pinned Pylint pass. Astra task-scoped review: approved, no blocking defect.
All older overlapping code/test/contract/doc hunks remain unstaged.
The complete architecture gate exposed an unused public collection resolver.
Astra approved retiring only that parent public declaration: its live router
caller stays inside the same component. The function/owner/signature remain.
Refreshed validation reports no contract-invalid diagnostics. The complete
architecture gate still FAILs: committed ArchKeel pin `20ee2979` observes
81 violations/167 unknown positions, 59 new baseline records and existing
ratchet failures (including typing 145 > 143). Released 0.8.1 observes
110/157 and 70 new baseline records on the clean checkpoint. Both observe all
491 files; neither passes the declared contract. Baseline/budgets stay unchanged.

All 491 product files matched Step 76 AFTER before edits. After edits, only
the eight IO API bindings/export-list entries differ; owner bodies/signatures
and all 930 XML files remain unchanged. No other product AST change.

Fresh dirty-integration capture: 930 inventoried; 383 CAPTURED, 70 expected
errors, 16 non-descriptors, 77 unrunnable, 384 unverified. All 109 captured
seeded results and all four projection records match Step 76 AFTER.
The unchanged frozen comparator remains FAIL: 478 differences, including
461 unverified/unrunnable, 16 captured comparisons and one stale projection
guard. Nine captured records lack sufficient shape evidence; seven other
unseeded differences still need adjudication. This is not full DSL parity.

Released ArchKeel 0.8.1 and report candidate
`0.8.2.dev27+g5d1506f11` (analyzer 0.60.0) produce identical canonical JSON.
Dirty integration: declared rules FAIL; observation PASS; violations
112 → 102, unknown-position count 158 → 155, typing positions unchanged at
145. Exactly ten duplicate FileUtil violations and eighteen raw UNKNOWN
records disappear; no new IDs. Reader-owner type coverage remains open.

Browser sampling: pure Target → IO → files shows its declared responsibility
and all three file modules; Actual retains that physical scope. Diff explicitly
falls back to global categories for this unindexed leaf. Full scoped Diff,
recursive semantic acceptance and human visual approval remain open. Evidence
screenshots are not approved publication imagery.

Oracle provenance: BEFORE `/private/tmp/ce-policy-after-step76.json`, AFTER
`/private/tmp/ce-io-after-step77.json`; frozen source
`/private/tmp/ce-io-after.DHxGAb`. Runner SHA256
`89a2b5482c21d2387e0a226426b1c09cff842211155f790a4f6537ab30807d42`;
comparator at `/private/tmp/ce-policy-after.51WUW2/script/architecture_study/compare_step0.py`
SHA256 `f71f37cf49e53063aa3e39e26bb06bf80120ecc64b7c25dac653c0c5fde16f39`.
The copied BEFORE Git metadata is stale; source fingerprints, not that commit
field, establish its provenance. BEFORE capture SHA256
`bf597ea62e7ee4982e7139e261310e20f1b22f564c9b1c798435a97f00c59a63`;
AFTER SHA256 `2f70b72ffb71bd007682158804696dd4a626039db40d1958881db933194c5bd0`.

CI-ONLY VERIFICATION: baseline run `36776134964` at `3a2fc282` completes with
architecture FAILURE; normal tests/build/lint/type/seeded-matrix lanes succeed.
E2E and release skipped. This step does not close global semantic/report or
descriptor acceptance.
