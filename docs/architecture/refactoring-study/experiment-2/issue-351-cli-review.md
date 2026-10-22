# Issue 351: independent Astra review

Accepted locally for source `fc8dc1c0677bf77c467bea7653c273639cff817b3cfc0f2b6902456bd793cddb` on HEAD `4161fa58e1b3c12628b8820d64253365ce68d165` plus the one-line CLI serializer fix. No source blocker found.

The CLI omitted `capture.requested` when its value was null, violating the public required-but-nullable field contract. Removing `exclude_none=True` from generic BaseModel serialization preserves the declared result shape. Models and schemas are unchanged. Dedicated Compile, Build and Decompile text branches are unchanged; the generic JSON fallback also retains null fields for `--format text`.

LOCAL VERIFIED: independently ran `test_cli_v4.py`: 13 passed. The real SQLite regression validates the complete output with public `RunResult`, checks bounded ordered rows, retains `requested: null`, and checks unchanged database bytes. The presenter SHA-256 is `c573ab3501e7b532cafb02cf3906b65757f50d3133f4767cbdcd7e06624d12f5` and was rechecked before receipt creation.

Native observation covers 534/534 files. Measurements remain 1431 unresolved calls, 178 typing positions, 253 unknown positions, 2 cycle edges, 0 private crossings and 0 violations. All 311 decoded UNKNOWN records exactly equal the previously reviewed issue-350 records. Their classifications and all 20 publication-usage diagnostics are preserved. Contract, analyzer and approved budgets are unchanged; no uncertainty is declared resolved.

Native validate exits 2 with declared rules UNKNOWN and no failures or baseline drift. The full architecture report exits 0. The receipt binds the current source and validation by digest and preserves the unchanged UNKNOWN digest. Historical human budget acceptances remain unchanged.

CI-ONLY VERIFICATION: current-fix full CI, external services, Windows and installed-package behavior are not independently established here. Build external includes remain unsupported; cross-descriptor memstore completeness and issue 281 cause remain UNKNOWN. Full CE complex-reference acceptance, native-client end-to-end behavior and public installation remain outside this review. Root owns final CI and merge decisions.

Independent completion gate: exit 0, `Architecture completion: 0 violations; 311 assessed UNKNOWN records remain.` Evidence: `astra-cli-completion-gate.log`.
