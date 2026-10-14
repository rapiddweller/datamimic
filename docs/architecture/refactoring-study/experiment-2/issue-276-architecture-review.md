# Issue 276: independent architecture review

**GO for the bounded CE architecture gate.** Reviewed by Astra, independent agent `/root/architecture_ci_review`, on 2026-10-14. Analyzed source commit: `f71f83d2ae29e347ed7aca5ba06448bf16952a53`; immutable comparison base: `6520b70d671295e17af159614127e19e9a5715d8`. This decision does not authorize merge or release.

Global increment remains a Runtime construction/storage concern. Runtime scheduling inspects statement vocabulary and resolved named instances through the existing published generator catalogue; it does not introduce a Domain-to-Runtime dependency. The corrected policy dispatch identifies its registered callable rather than routing on a descriptive string. Mapping[str, object] exposes the existing heterogeneous generator registry to internal scheduling and remains a bounded internal typing limitation.

The pinned published ArchKeel 2.0.0 / Python 3.11.12 evidence has complete observation and AST coverage, zero violations and no baseline additions or resolutions. All 20 exact publication-usage diagnostics remain assessed uncertainty. The complete 286 UNKNOWN inventory is independently reassessed in 45 groups, each ID exactly once; the six historical source-contract debt IDs remain explicit. UNKNOWN is not PASS.

Only the global dynamic-call count differs among286UNKNOWN records. Three added unresolved calls are generator-expression strip/split operations whose receivers derive from the annotated DSL string property (total1249). The fixed source removes the private GlobalIncrementGenerator import, resolves its nominal type from the already-public RUNTIME_GENERATOR_TYPES catalogue, preserves isinstance alias/subclass semantics, and dispatches the special callback by callable identity. Native evidence now has zero violations with unchanged contracts; the original private-import and descriptive-label-routing defects are resolved. The comparison found 1 changed records, no removed IDs and no added IDs. Current unresolved calls: 1249. Every group's fresh rationale, record digest and changed-record inventory is in `completion-unknowns.json`.

| Evidence | Exact digest |
|---|---|
| Source | `c075fc670ebdd3e24ff64f2c7448ce0e508c1ff82b72344b68c271ed980c0e4c` |
| Target contracts | `289d6c0ee28d75e53e7ed8d057edbd66dd4004c5c362b6cccf5f7c095e0f7745` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `f2ce89cbf1a6d80ecd3096822b87e8bb532dff9e3c29cd9821d10284e3bb1bfe` |
| Complete UNKNOWN records | `341b0e0103929fcd1c388af4809dc218d16d8c442f8fdac261a82ce59e605907` |

Method: inspect the retained target/protocol/amendment 20, all 45 frozen groups and current source differences; verify affected owner/import/signature routes, source-debt bodies and publication bindings; compare native base/current records and diagnostics; inspect changed dynamic-call evidence; then run the unchanged completion gate against this newly authored assessment. That exact gate returned 286 assessed UNKNOWN records. Native artifacts and provenance hashes are recorded in the receipt.

Limitations: this review establishes the bounded structural/semantic acceptance described above. It does not rerun product behavior, prove dynamic-call completeness, close inherited/alias/property surfaces, or discharge retained debt. CI and behavioral evidence remain separate judgments.
