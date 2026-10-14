# Issue 287: independent architecture review

**GO for the bounded CE architecture gate.** Reviewed by Astra, independent agent `/root/architecture_ci_review`, on 2026-10-14. Analyzed source commit: `762fedf44fc2302d5be1ec74f1a398948187e8d2`; immutable comparison base: `6520b70d671295e17af159614127e19e9a5715d8`. This decision does not authorize merge or release.

Runtime invokes the existing zero-argument generator interface consistently in lazy construction and subsequent mode execution. Removing the SequenceTableGenerator-specific dependency reduces coupling; sequence construction already captures its context. No source/connector policy moves owners. The unused inner construction publication for SequenceTableGenerator is retired because its remaining class imports are within the construction owner; the implementation, factory catalogue and descriptor name remain intact. This narrows the declared cross-component surface without adding permissions.

The pinned published ArchKeel 2.0.0 / Python 3.11.12 evidence has complete observation and AST coverage, zero violations and no baseline additions or resolutions. All 20 exact publication-usage diagnostics remain assessed uncertainty. The complete 286 UNKNOWN inventory is independently reassessed in 45 groups, each ID exactly once; the six historical source-contract debt IDs remain explicit. UNKNOWN is not PASS.

All286UNKNOWN records and decoded unresolved-call facts equal the native base (1246). Removing the obsolete SequenceTableGenerator special case makes its construction class publication unused; the reviewed target now removes only that exact inner public entry. Factory/catalogue/DSL behavior remains present, and the fresh report has only the20originalusage_unknown diagnostics. This is a justified retirement of an unused cross-owner surface, not an added boundary permission or relabeling of interface.unused. The comparison found 0 changed records, no removed IDs and no added IDs. Current unresolved calls: 1246. Every group's fresh rationale, record digest and changed-record inventory is in `completion-unknowns.json`.

| Evidence | Exact digest |
|---|---|
| Source | `857b5ac1562932511e3134cfa7761d4d7558c4c50c670fb91cac2f429487e4ce` |
| Target contracts | `6e286ba09c32ee1ff38c4238e0d6a589ab07972657e9bebf770a91050b8f832e` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `f4f4b56a4b3e3b43d1adffb268524d7539415795b89724e8cb046c9f5bba60d5` |
| Complete UNKNOWN records | `612725aab375502e431b6b295381e9ec123d709bd8c96b0e4ec0273c9189847d` |

Method: inspect the retained target/protocol/amendment 20, all 45 frozen groups and current source differences; verify affected owner/import/signature routes, source-debt bodies and publication bindings; compare native base/current records and diagnostics; inspect changed dynamic-call evidence; then run the unchanged completion gate against this newly authored assessment. That exact gate returned 286 assessed UNKNOWN records. Native artifacts and provenance hashes are recorded in the receipt.

Limitations: this review establishes the bounded structural/semantic acceptance described above. It does not rerun product behavior, prove dynamic-call completeness, close inherited/alias/property surfaces, or discharge retained debt. CI and behavioral evidence remain separate judgments.
