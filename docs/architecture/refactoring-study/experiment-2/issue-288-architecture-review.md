# Issue 288: independent architecture review

**GO for the bounded CE architecture gate.** Reviewed by Astra, independent agent `/root/architecture_ci_review`, on 2026-10-14. Analyzed source commit: `4114ca558ce0095a9f1970bccd48e10965d31ccc`; immutable comparison base: `6520b70d671295e17af159614127e19e9a5715d8`. This decision does not authorize merge or release.

The new contexts/products.py is owned and explicitly published by Runtime contexts, with exact root-layout admission and structure-review rationale. ExecutedExport carries typed product/destination/targets, NestedExport carries actual executed statement/rows/children, and GenerationResult carries page/worker metadata without starting workers or constructing clients. Its imports use existing DSL/IO APIs; no task dependency is introduced into contexts. Runtime retains conditional execution/order/finalization timing; IO retains exporter registration, buffers and dispatch. The dict[str, list] compatibility carrier and native row payloads retain unproved internal typing, not a new global opacity allowance. Only the exact new module is admitted; no baseline, dependency prohibition or type grant is weakened.

The pinned published ArchKeel 2.0.0 / Python 3.11.12 evidence has complete observation and AST coverage, zero violations and no baseline additions or resolutions. All 20 exact publication-usage diagnostics remain assessed uncertainty. The complete 286 UNKNOWN inventory is independently reassessed in 45 groups, each ID exactly once; the six historical source-contract debt IDs remain explicit. UNKNOWN is not PASS.

Two PreparedPage UNKNOWNs change only fact/evidence references after ExportSession moved methods; their aliases and signatures are unchanged. The IO aggregate increases decided positions205->206 and total258->259 for the new optional str execution_id parameter; no UNKNOWN position is added. Eight new unresolved calls concern typed export carrier dict/set/list operations, dataclass cls construction, dict base initialization and export_uri.encode (total1254); four apparent call differences are comprehension-line shifts. The new products module is explicitly owned and admitted without raising budgets or adding opacity permissions. Its exact Runtime-context placement and existing DSL/IO API dependencies are approved; native report observes489/489Python files. The comparison found 4 changed records, no removed IDs and no added IDs. Current unresolved calls: 1254. Every group's fresh rationale, record digest and changed-record inventory is in `completion-unknowns.json`.

| Evidence | Exact digest |
|---|---|
| Source | `66e6b272f234b1e3d2f6829dc4956893557387c5c1023388898f9f1180d79509` |
| Target contracts | `ff897df420a8be4e4deb758fe4032beb3309c559f72bb089a3ae7800e3c7f0e3` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `bdc90fcb7329f1ad21c87ddb7795c0cc69164f56e973d3821178a6ad574138cf` |
| Complete UNKNOWN records | `ff7ed8a7260f9c1905e0325e17f4b1ea40fede976d59d4f1a071b44733cf63ed` |

Method: inspect the retained target/protocol/amendment 20, all 45 frozen groups and current source differences; verify affected owner/import/signature routes, source-debt bodies and publication bindings; compare native base/current records and diagnostics; inspect changed dynamic-call evidence; then run the unchanged completion gate against this newly authored assessment. That exact gate returned 286 assessed UNKNOWN records. Native artifacts and provenance hashes are recorded in the receipt.

Limitations: this review establishes the bounded structural/semantic acceptance described above. It does not rerun product behavior, prove dynamic-call completeness, close inherited/alias/property surfaces, or discharge retained debt. CI and behavioral evidence remain separate judgments.
