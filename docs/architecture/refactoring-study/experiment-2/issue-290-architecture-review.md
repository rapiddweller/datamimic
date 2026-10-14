# Issue 290: independent architecture review

**GO for the bounded CE architecture gate.** Reviewed by Astra, independent agent `/root/architecture_ci_review`, on 2026-10-14. Analyzed source commit: `18806c3e698a4095670e8379b2738fe1ea5d59bf`; immutable comparison base: `6520b70d671295e17af159614127e19e9a5715d8`. This decision does not authorize merge or release.

MongoDBClient now implements its count_table_length adapter by delegating to its existing count operation and declaring int. Counting stays inside the IO client owner; no Runtime-specific database access or registry narrowing is introduced.

The pinned published ArchKeel 2.0.0 / Python 3.11.12 evidence has complete observation and AST coverage, zero violations and no baseline additions or resolutions. All 20 exact publication-usage diagnostics remain assessed uncertainty. The complete 286 UNKNOWN inventory is independently reassessed in 45 groups, each ID exactly once; the six historical source-contract debt IDs remain explicit. UNKNOWN is not PASS.

All286UNKNOWN records and decoded unresolved-call facts equal the native base (1246). MongoDB count_table_length is now explicitly int-returning and delegates to existing count within its IO owner; RegisteredClient facade uncertainty remains unchanged. No ownership, target or analyzer drift occurs. The comparison found 0 changed records, no removed IDs and no added IDs. Current unresolved calls: 1246. Every group's fresh rationale, record digest and changed-record inventory is in `completion-unknowns.json`.

| Evidence | Exact digest |
|---|---|
| Source | `bd3e22e6cc0fb9059f901ab6a5c026829b0cbf6252f9fcb8734820b9142698fe` |
| Target contracts | `289d6c0ee28d75e53e7ed8d057edbd66dd4004c5c362b6cccf5f7c095e0f7745` |
| Analyzer payload | `7106e3595fa7df9269cb43ee280f9c557659db7bda171b1f65ff5619ab54aa24` |
| Validation | `00b0e69ae6f05ac7fcfca9d20edd06397657431ac4572cc4370e020f8ee36a35` |
| Complete UNKNOWN records | `612725aab375502e431b6b295381e9ec123d709bd8c96b0e4ec0273c9189847d` |

Method: inspect the retained target/protocol/amendment 20, all 45 frozen groups and current source differences; verify affected owner/import/signature routes, source-debt bodies and publication bindings; compare native base/current records and diagnostics; inspect changed dynamic-call evidence; then run the unchanged completion gate against this newly authored assessment. That exact gate returned 286 assessed UNKNOWN records. Native artifacts and provenance hashes are recorded in the receipt.

Limitations: this review establishes the bounded structural/semantic acceptance described above. It does not rerun product behavior, prove dynamic-call completeness, close inherited/alias/property surfaces, or discharge retained debt. CI and behavioral evidence remain separate judgments.
