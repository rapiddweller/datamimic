# Combined CE merge: independent architecture review

**GO for the bounded CE architecture completion rule.** Reviewed independently by Astra, task `/root/astra_merge_architecture`, on 2026-10-14. Exact analyzed clean source: `332fc05a49fcdca5120ead1d9ecc2b49a4bcbf19`, branch `codex/ce-reviewed-merge-local`. The native evidence uses published ArchKeel 2.0.0 and Python 3.11.12; analyzer payload identifies version 0.74.0. This review assesses the combined source and architecture. Merge authorization remains the user's separate instruction.

The unchanged completion gate accepts the new [UNKNOWN receipt](completion-unknowns.json): zero native violations, complete observation/coverage, zero baseline additions or resolutions, and every one of 286 UNKNOWN records assessed exactly once. All 20 `interface.usage_unknown` validation diagnostics are preserved and assessed. The full architecture projection itself remains UNKNOWN with no ownership gaps; this is bounded acceptance, not a claim that uncertainty became PASS.

| Evidence | Exact digest |
|---|---|
| Source | `f33f1e4473dfbae007c8ac0f88b7258110fbafe40150db2073d0afe37adbcf88` |
| Target contracts | `08a8909a96bf313f6f88229b1b17642a851aa5c61d87263ca53be4e37c801321` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `6b9081a1fdff57526fec2169fa5be7deb76caad654a2ded601bd45c7eaa812c7` |
| Complete UNKNOWN records | `0efae6460863294e1125a99915b7051a9688be7a4eff73ef8c1bb2a9b079374e` |

## Combined source and ownership

I independently verified that the exact reviewed original heads of all 18 PRs #308–325 are ancestors of this head. `datamimic_ce` and `docs/architecture/inner` match the previous aggregate `fce8eb59f67a251a529e0e449a1dcb2464afc471`; that equality is context, not a substitute for this review or a fresh behavioral proof.

The two code conflict resolutions preserve compatible state scopes. `GenIterContext.pending_exports` starts empty for each row. `unique_cursors` is supplied from a generate-invocation map shared across pages; nested generate calls obtain a new map, and same-named conditional fields use statement identity. The worker carries both state structures through its combined signature. Completed rows contribute their actual nested exports to `GenerationResult`, and export ordering consumes those executions rather than reconstructing active branches from shared names. Worker merges preserve executed export destinations and worker IDs for finalization. File/export conversion remains IO-owned and ordering remains Runtime-owned.

The new `runtime.contexts.products` carrier has an explicit module concern, exact layout admission and public decision in the existing Runtime-context owner. It imports declared DSL/IO APIs and introduces no task-orchestration dependency into contexts. Removal of the unused SequenceTableGenerator publication narrows the existing values-construction surface. The root ownership target, gate, baseline, analyzer pins and opacity permissions were not weakened.

The lifecycle document retains both global-increment and named-state-machine sections. Factory selection distinguishes definitions that create per-field walks from explicitly registered instances that share a walk. Global-increment aliases remain recognized by the serial policy. Their documented include and worker scopes remain explicit; neither section grants a descriptor-wide cross-worker sequence guarantee.

## Current uncertainty assessment

I read AGENTS, the retained target/protocol, completion gate, current contracts and conflict source before the native records. I then inspected all 286 records and all validation diagnostics, reconciled each aggregate's complete position list, and only afterward consulted the earlier receipt to preserve useful group continuity. The 45 groups have newly written reasons tied to current source; previous activation metadata and stale measurements were not carried forward. Native columnar IR was independently decoded and its complete UNKNOWN objects matched the completion projection exactly.

The inventory consists of 267 boundary positions, seven reexport routes, six boundary aggregates, four API-surface records and two global observation limits. Current aggregate position counts are IO 53, Authoring 7, Resources 1, Domains 72, Runtime 66 and DSL 68. The six explicit missing-annotation obligations remain: `Statement.get_parent_full_name`, three Memstore method positions, `RdbmsConnectionConfig.get_connection_config`, and the `SetupContext.generators` setter. The bare-dict generators getter remains additional open-map uncertainty. Inherited/property bindings, generic/recursive aliases and external-library surfaces remain unresolved.

Validation's 20 diagnostics cover 16 subjects: the real LeafFieldKind alias and 15 BaseEntity subclasses. The alias is used in the authoring schema; the model sources contain no direct class-body control-flow statement. Their inherited/property/publication routes nevertheless remain unproven. These diagnostics are neither missing-definition findings nor certificates that every published field is used and closed.

Coverage is 489/489 Python files, 100% AST coverage, and 73.76% call resolution: 11,881 analyzed calls, 8,763 resolved, 1,857 partially resolved and 1,261 unresolved. The native comparison base has 1,246 unresolved calls. A decoded multiset comparison found 29 added and 14 removed scope-qualified unresolved facts; 14 pairs are location-only comprehension/lambda shifts, leaving 15 new unresolved expressions in alias policy, export metadata, generator initialization and CLI parsing. Source inspection found no ownership violation in those expressions. Arbitrary dynamic dispatch and alias dataflow remain unproven.

Measured typing positions improve from native base 147 to merged 146. The unchanged historical budget is 143, so this review does not claim every historical scalar budget is met; the combined source introduces no new typing-position regression against this native base. Unresolved calls remain below their unchanged 1,278 budget. Native cycle edges remain 2, private crossings 0, untyped private accesses 0 and unknown positions 233. None of these measurements was rewritten to obtain acceptance.

## Verification and limits

The unchanged `tests_ce/architecture/completion_gate.py` returned: `Architecture completion: 0 violations; 286 assessed UNKNOWN records remain.` The receipt stores the exact native artifact SHA-256 hashes as additional provenance.

An independent bounded probe combined global-increment aliases, requested two-worker configuration (correctly reduced to serial), same-named conditional child exports to odd/even destinations, finite unique values 1–4, nested page size 2, parent page sizes 1 and 3, and buffered JSON chunk size 3. Both cases produced the expected 16 child rows, correct destination/parent association, one complete unique pool per nested invocation, and equal final contents across parent page sizes. The probe wrote only temporary files and touched no shared database. Its script and log are retained externally under `/workspace/ce-results/merge/architecture/reviewed/combined_probe.py` and `combined_probe.log`.

The coordinating agent separately reports 2,544 unit tests passed with 11 skips and two existing Pydantic warnings, 179 functional/integration checks passed, 10 local PostgreSQL/Mongo/Memstore owner checks passed, full Ruff passed, and MyPy passed on 489 files. I did not duplicate those broad suites; they remain separate behavioral evidence.

No blocking combined architecture/conflict defect was found within this scope. This review does not discharge residual source-contract debt, prove all dynamic calls or inherited surfaces, certify every payload/vendor/backend/EE behavior, or establish universal behavior preservation. The bounded probe did not execute Ray or multiprocessing workers. Product source changes require new native evidence and review; installing this note and receipt alone changes no analyzed Python source or architecture target.
