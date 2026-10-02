# Step 78: Native Runtime capture

Runtime returns IO's existing capture dictionary directly, without a validating
wrapper, copy or conversion. Python adapters and factory consumers use it
directly. Authoring keeps its separate bounded evidence and worker-side IPC
normalization. Empty captures, accumulation and native object identity stay.

Independent Luna implementation and QA; Astra design/review; root integration,
contracts and Git. Product changes span six files; QA owns two test files.
Older overlapping contract and smoke-export edits are excluded from this slice.
No descriptor, oracle, baseline, budget or dependency-rule change.

CE 5.0 deliberately breaks the Runtime `CapturedProducts` import and `.root`
access: session capture and `run(...).captured` now expose
`dict[str, list[dict[str, object]]] | None`. Repository consumers are migrated;
external consumers are UNKNOWN. DataMimic/factory output compatibility is not
proof of external Runtime-import compatibility. No compatibility shim.

LOCAL VERIFIED: behavioral RED against the old wrapper; 73 focused tests;
exact clean Step77 plus this slice: 1539 unit passes, 11 skips, 1 xfail,
two existing serializer warnings; Ruff, MyPy (491 files), pinned Pylint
executable-cycle check and 12 recursive/inner/cold-entry checks pass.
The archive needed explicit read-only Git metadata for Git-dependent tests.

Released ArchKeel 0.8.1 initially reports three new findings, all in
`runtime.api.run` at `return.captured`: the outer dictionary, row dictionary
and opaque `object` leaf. Clean checkpoint: 110 -> 113 violations, UNKNOWN157
unchanged. Dirty integration: 102 -> 105, UNKNOWN155 unchanged. These are real
contract findings, not false positives or repaired types. Astra approves only
the explicit capture-data amendment described in [Amendment 82](amendment-82.md);
the amendment restores exactly those three permissions. Released clean report:
110 violations/157 counted UNKNOWN; dirty integration: 102/155. All 215 raw
integration UNKNOWN records are identical. Two isolated negative probes still
report new violations for public `run.extra_control` and `RunResult.control`.
An initial control probe touched only the internal runner, not the public
boundary; the corrected API probe is the authoritative negative evidence.
Independent QA: the exact permission guard and 13 existing Runtime tests pass.
The full architecture gate remains FAIL; no accepted baseline is changed.

Dedicated Docker/Orbstack tests, serial and frozen: eight reference cases plus
one Mongo multiprocessing case pass on old/new (nine AFTER passes); the 13
Postgres/Mongo storage tests also pass on both. They reinitialize only their
own tables/collections. This tests existing invariants, not full persisted
old/new output parity. Static service inventory maps 213/224 descriptors to
owner tests, with 11 owner and 117 backend mappings UNKNOWN; every inventory
row remains UNVERIFIED until its acceptance evidence is evaluated.

Frozen descriptor inventory: 930 total; 383 CAPTURED, 70 EXPECTED-ERROR,
16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE, 384 UNVERIFIED. All 109 captured seeded
records and all four projection records exactly match Step77. The unchanged
frozen comparator remains FAIL: 479 differences, 3 tolerated. Its 461
unverified/unrunnable records, nine insufficient capture shapes, eight
unseeded structural differences and one stale projection guard prevent full
DSL parity acceptance. No oracle threshold is relaxed.

Oracle: BEFORE `/private/tmp/ce-io-after-step77.json`; AFTER
`/private/tmp/ce-native-after-step78.json`; frozen AFTER source
`/private/tmp/ce-native-after.21zhPo`. Runner SHA256
`89a2b5482c21d2387e0a226426b1c09cff842211155f790a4f6537ab30807d42`;
frozen comparator SHA256
`f71f37cf49e53063aa3e39e26bb06bf80120ecc64b7c25dac653c0c5fde16f39`.

CI-ONLY VERIFICATION: none for Step78. Step77 run36783256508 at7154224f
FAILs architecture and one Mongo multiprocessing connection timeout;
other behavioral test jobs succeed. The isolated Mongo case passes locally,
but the CI timeout cause remains UNKNOWN. No global completion or merge.
