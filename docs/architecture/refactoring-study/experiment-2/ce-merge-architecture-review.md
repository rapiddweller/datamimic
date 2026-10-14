# Combined CE merge and clinical-demo follow-up: independent architecture review

**GO for bounded CE architecture completion; the orphan-demo P2 is fixed.** Reviewed by Astra (`/root/astra_merge_architecture`) on 2026-10-14. Exact clean analyzed source: `abcb5ca09dc34c5f012af195b2e6ba1a8dc3b6cd`. Fresh native evidence uses published ArchKeel 2.0.0 / Python 3.11.12, with analyzer payload 0.74.0. This supersedes the earlier source-bound receipt; merge authorization remains the user's separate instruction.

The full report and unchanged completion gate establish zero violations, complete observation/coverage, zero baseline additions/resolutions, and independent assessment of all 286 UNKNOWNs exactly once in 45 groups. All 20 `interface.usage_unknown` diagnostics remain assessed uncertainty. The architecture projection remains UNKNOWN, with no ownership gaps. UNKNOWN is not PASS.

## Follow-up resolution

After removal of the clinical-trial descriptor, its remaining helper directory was still returned by `demo_names`, offered by autocomplete and copied by `demo create --all`. The native CLI regression failed on that orphan name before the fix. The committed resolution moves the helper to `resources/examples/generate_clinical_cohort.py`; Git reports 100% similarity, and the unchanged bytes hash to `3c338b0598da99ae430816d2b255804af3bd995963a350889ff389c3bcf693b4`. The old demo directory is absent. The helper remains Resources-owned and uses its existing Domains API dependency.

The target adds exactly that examples child and updates the module concern path. The historical source existed at the manifest's frozen commit and is truthfully linked through one relocation record. Historical semantic-review records remain unchanged; the file is neither fabricated as a new module nor erased from history.

I independently reviewed the architecture-check adjustment. `_target_files` still validates every selector against the complete frozen source and retains collision checks. `_partition_target_files` then applies existing exclusions to mapped target paths. Three callers now use this order; source-side historical package reviews retain their original scope. Thus an excluded demo source moved into an included example is checked as a current core target. The new bounded regression proves source provenance, retained excluded targets, missing moved-target detection and rejection of an invalid excluded-source selector. This corrects inconsistent filter order without weakening the existing selector/ownership gate.

The CLI regression checks that the orphan is absent from discovery/autocomplete, `create --all` succeeds, copied directories match the discovered inventory, and every copied demo has `datamimic.xml`. Reviewed logs show 45 CLI tests and 38 architecture controls passed, full Ruff passed and MyPy passed on 489 files. These checks establish inventory/copy correctness and descriptor existence, not successful execution of every bundled demo.

## Fresh evidence and retained uncertainty

| Evidence | Exact digest |
|---|---|
| Source | `ca4feeac489462a75bfc10d98a0a34498d562f6af037f1dd1ddbb916b907ec01` |
| Target contracts | `4b4fd0ba1f77f60115d3e2d4ccb973391de7ab973f5cec60fc86d5ac699310c4` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `6b9081a1fdff57526fec2169fa5be7deb76caad654a2ded601bd45c7eaa812c7` |
| Complete UNKNOWN records | `0efae6460863294e1125a99915b7051a9688be7a4eff73ef8c1bb2a9b079374e` |

All current native UNKNOWN objects were independently decoded and matched the full completion projection. Every record also exactly matches the earlier independently inspected inventory; all 45 group digests were rechecked. Current source change is solely the byte-preserving helper rename. All 20 validation diagnostics and the complete parsed validation JSON are unchanged. The seven changed call-source routes belong to the relocated helper: six resolved calls and one partially resolved service call. Expressions, statuses and reasons are unchanged; no unresolved call was added or removed. This assessment uses fresh source/contract binding rather than asserting the old scan as current evidence.

The inventory retains 267 boundary positions, 7 routes, 6 aggregates, 4 API-surface records and 2 global limits. Six explicit missing-annotation obligations remain: `Statement.get_parent_full_name`, three Memstore positions, `RdbmsConnectionConfig.get_connection_config`, and the `SetupContext.generators` setter. The bare-dict generator getter remains additional open-map uncertainty. All inherited/property, external-type, generic and recursive-alias limitations remain in the receipt with source-specific reasons.

Native coverage remains 489/489 Python files and 100% AST coverage, with 11,881 analyzed calls: 8,763 resolved, 1,857 partially resolved and 1,261 unresolved (73.76% resolution). Typing positions remain 146, improved from the earlier native base 147 but above the unchanged historical 143 budget. No new typing-position regression is introduced; this is not a claim that every historical scalar budget is met. Unresolved calls remain below the unchanged 1,278 budget. Cycle edges remain 2, private crossings 0, untyped private accesses 0 and unknown positions 233.

The original combined merge semantics remain unchanged: invocation-scoped finite cursors survive pages, nested invocations receive separate cursors, row-local pending exports carry actual conditional executions, and worker result metadata preserves destinations for finalization. The Runtime-context products carrier retains explicit ownership/public/layout decisions; IO owns conversion and Runtime owns export ordering. Global-increment and named-state-machine lifetime documentation remains intact. The earlier bounded combined runtime probe passed on the previous analyzed source; the follow-up changes no Runtime bytes. That earlier probe and coordinator-run broad/service suites are historical supporting evidence, not fresh full-suite execution at this head.

## Decision and limits

The new receipt passes the unchanged completion gate: `Architecture completion: 0 violations; 286 assessed UNKNOWN records remain.` The baseline, analyzer pins, allowed dependencies, opacity permissions and completion-gate code are unchanged. The only target changes admit the exact relocated resource module and move its concern. Raw artifact hashes are recorded in the receipt.

No blocking architecture, relocation, filtering or demo-discovery defect remains within this review. The helper was not executed as a cohort-generation benchmark; the focused CLI checks do not prove every demo's runtime behavior. Residual source-contract debt, dynamic dispatch, inherited surfaces, backend/vendor/EE behavior and universal payload equivalence remain outside this bounded acceptance. Product-source changes require fresh native evidence and review.

The full earlier aggregate review, its combined probe and coordinator verification evidence, and its explicit limits remain preserved in the [prior committed review](https://github.com/rapiddweller/datamimic/blob/08f09a9dd5ce6c95d272095605853cb56f5a92d9/docs/architecture/refactoring-study/experiment-2/ce-merge-architecture-review.md). That historical source binding is retained as context, while this receipt binds the fresh follow-up scan.
