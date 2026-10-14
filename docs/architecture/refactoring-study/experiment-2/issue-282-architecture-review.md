# Issue 282: independent architecture review

**GO for the bounded CE architecture gate.** Reviewed by Astra, independent agent `/root/architecture_ci_review`, on 2026-10-14. Analyzed source commit: `f88936939318a2192c1200708ced28d0cce15bc1`; immutable comparison base: `6520b70d671295e17af159614127e19e9a5715d8`. This decision does not authorize merge or release.

Runtime owns invocation-scoped cursor lifetime across pages and task rebuilding; nested-key scopes reset locally. IO owns distinct-value selection and bounded exhaustion through the existing public unique_value_iter operation; the attempted private unique_values facade export has been removed. Bare dict cursor stores add visible internal typing debt (statement-identity keys and iterator values), not a closed new DTO or a permission to loosen facade types. The final IO facade is identical to base; its original TypeVar UNKNOWN positions remain and no new facade positions are introduced.

The pinned published ArchKeel 2.0.0 / Python 3.11.12 evidence has complete observation and AST coverage, zero violations and no baseline additions or resolutions. All 20 exact publication-usage diagnostics remain assessed uncertainty. The complete 286 UNKNOWN inventory is independently reassessed in 45 groups, each ID exactly once; the six historical source-contract debt IDs remain explicit. UNKNOWN is not PASS.

The final source uses the existing public unique_value_iter and removes the private unique_values facade addition. Both original failures (private IO crossing and unused iterator publication) are absent. All286UNKNOWN records and decoded unresolved-call facts equal the native base (1246). Invocation-scoped bare-dict cursor state remains explicit internal typing debt; it grants no new facade opacity. Target contracts are unchanged. The comparison found 0 changed records, no removed IDs and no added IDs. Current unresolved calls: 1246. Every group's fresh rationale, record digest and changed-record inventory is in `completion-unknowns.json`.

| Evidence | Exact digest |
|---|---|
| Source | `150b63136bda7a1178cc987ac54a3a988c40be68e8c1c0b4a86c8c713be0f28d` |
| Target contracts | `289d6c0ee28d75e53e7ed8d057edbd66dd4004c5c362b6cccf5f7c095e0f7745` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `6bfde277aad3ca3211ef06f7cb1c43458cec2326bcdf01dcc7d841225314a7f0` |
| Complete UNKNOWN records | `612725aab375502e431b6b295381e9ec123d709bd8c96b0e4ec0273c9189847d` |

Method: inspect the retained target/protocol/amendment 20, all 45 frozen groups and current source differences; verify affected owner/import/signature routes, source-debt bodies and publication bindings; compare native base/current records and diagnostics; inspect changed dynamic-call evidence; then run the unchanged completion gate against this newly authored assessment. That exact gate returned 286 assessed UNKNOWN records. Native artifacts and provenance hashes are recorded in the receipt.

Limitations: this review establishes the bounded structural/semantic acceptance described above. It does not rerun product behavior, prove dynamic-call completeness, close inherited/alias/property surfaces, or discharge retained debt. CI and behavioral evidence remain separate judgments.
