# ArchKeel 3.0.1: independent upgrade review

**GO for the bounded checker upgrade and separate PR.** Reviewed by Astra (`/root/astra_archkeel_301_review`) on 2026-10-15. No blocking finding remains. This review does not authorize a merge.

Published ArchKeel 3.0.1 with Python 3.11.12 analyzed clean source `f8ac7a8c422017bc77a740519915224465abb5e3`. The reviewed integration commit `a446c2db47bd7502f1e1faa021de86e4c1b85692` changes only the Makefile checker pin, current CI documentation, publisher test fixtures and one stale architecture test. Git confirms that its analyzed CE source, target contracts, baseline and completion policy are identical to the clean scan. The receipt deliberately identifies the actual analyzed commit. Adding this review and receipt does not alter the analyzed source or contracts.

## Compatibility and implementation

The package major reflects command-result 8.0.0 compatibility changes, including incomplete observations with confirmed FAIL. This repository consumes native fields and verdicts without validating against the older command-result 6/7 schemas. Its full architecture projection still reports schema `2.0.0`; the completion gate correctly retains that exact requirement. CLI arguments, pinned Python, report paths, native exit handling, budgets and UNKNOWN policy are unchanged.

The publisher already derives the accepted package version from Makefile. Its updated fixture accepts 3.0.1, and the rejection test explicitly covers stale 2.0.0 metadata. Existing CI pin-provenance tests continue to verify that report generation, validation and metadata share the checker pin.

The pre-existing nested-export assertion referenced the removed `xml_result` parameter after the merged execution-metadata change. Its correction checks the actual `export: NestedExport` parameter and `NestedExport.rows: list[dict[str, object]]`, preserving the intended native XML row shape. No runtime, authoring, payload or error behavior is edited.

## Independent native evidence

All 21 decoded native record sections exactly match the preceding 2.0.0 scan on identical CE source and contracts. This includes 31,622 evidence records, 11,881 calls, 4,522 imports, 1,775 dependency edges, 278 typing signals and all 286 UNKNOWN records. The complete UNKNOWN projection equals the decoded native inventory, and all 45 group digests and exact-once assignments were independently revalidated. Prior classifications remain applicable because the actual records and source were checked, rather than assuming analyzer equivalence from a package version.

The analyzer payload digest changed from `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` to `a9e159db0a1912171ba9ec7abe8a60aac53d1e865159acfc88686bd451741ef0`, although its internal version label remains `0.74.0`. The receipt binds the new digest. Validation populates the previously null fields `open_decision_count: 0` and `open_decisions_complete: true`; all 20 `interface.usage_unknown` diagnostics, rule assessments, measurements, budget messages and native exit code 2 are unchanged. The complete validation object receives a new digest.

| Evidence | Digest |
|---|---|
| Source | `ca4feeac489462a75bfc10d98a0a34498d562f6af037f1dd1ddbb916b907ec01` |
| Target contracts | `4b4fd0ba1f77f60115d3e2d4ccb973391de7ab973f5cec60fc86d5ac699310c4` |
| Analyzer payload | `a9e159db0a1912171ba9ec7abe8a60aac53d1e865159acfc88686bd451741ef0` |
| Validation | `8ec476e4cdafd50bcff63d40950748eae597abc8d8d6223264251c4b524df7ce` |
| Complete UNKNOWN inventory | `0efae6460863294e1125a99915b7051a9688be7a4eff73ef8c1bb2a9b079374e` |

The unchanged completion gate accepts the new receipt: `Architecture completion: 0 violations; 286 assessed UNKNOWN records remain.` Observation and coverage are complete, baseline additions/resolutions are zero, and ownership gaps are empty. Both native declared rules and architecture projection remain UNKNOWN.

## Retained limits and verification

The inventory retains 267 boundary positions, 7 routes, 6 aggregates, 4 API-surface records and 2 global limits. All six concrete missing-annotation obligations remain: `Statement.get_parent_full_name`, three Memstore positions, `RdbmsConnectionConfig.get_connection_config`, and the `SetupContext.generators` setter. The generator getter's bare `dict` remains additional open-map debt. Current source inspection confirms those obligations. The 20 publication diagnostics cover the real LeafFieldKind alias and 15 BaseEntity model subclasses; inherited/property/alias publication remains unproved.

Coverage is unchanged at 489/489 files and 100% AST coverage. Of 11,881 calls, 8,763 are resolved, 1,857 partially resolved and 1,261 unresolved (73.76% resolution). Typing positions remain 146 against historical budget 143. The native budget messages also retain unresolved calls 1278→1261, cycle edges 11→2 and untyped private accesses 3→0. No budget is rewritten, and acceptance does not claim that every historical scalar budget is met. The upgrade introduces no measured regression on this source.

Reviewed coordinator logs show 1,724 architecture/publisher tests passed, 14 skipped, full Ruff passed, MyPy passed for 489 files, and the wheel-package smoke test passed. Both focused pre-fix failures were observed. The reviewer independently executed the native comparison and unchanged completion gate. These checks establish the bounded checker integration; they do not establish fresh full behavioral, database, vendor or Enterprise equivalence.

The [prior CE merge review](ce-merge-architecture-review.md) remains historical evidence with its original source and analyzer binding. All inherited surfaces, generic/recursive aliases, external types, dynamic dispatch and arbitrary dataflow limits remain open. Any future product-source or target-contract change needs matching native evidence and independent reassessment.
