# Issue 350: independent Astra review

Accepted locally for source `d059af8dee734c135e4a654efcc3ba09ff8440f1c2a1c3f137ad740371a2b58e` on HEAD `9589810e57bdb81c8a6b825e6da4f8896332c450` plus the four-file loader fix. No source blocker found.

The existing optional profile loader now reaches included descriptor parsing through SetupTask and SetupContext, including deepcopy. Root and included parsing use the same fallback. The bounded loader retains workspace containment and profile-name validation. No new loader abstraction, global mutable state or cache is introduced.

LOCAL VERIFIED: independently reran all six SQLite controls (inline/one/two includes, with/without profile): 6 passed, 21 deselected. They check capped rows and unchanged workspace bytes. Reviewed production file hashes are frozen in `astra-profile-source-hashes.json` and rechecked before receipt creation.

Native observation covers 534/534 files. Measurements remain 1431 unresolved calls, 178 typing positions, 2 cycle edges, 0 private crossings and 0 violations. Unknown positions increase 252 -> 253. The report contains 311 UNKNOWNs: all previous 310 IDs remain; the sole addition is `UNKNOWN-BOUNDARY-TYPE-POSITION-b8fd253c8df2829d`, classified generic because the new public SetupContext parameter has the explicit annotation `Callable[[Path, str], dict[str, str]] | None`. This is retained uncertainty, not missing typing. Contract and analyzer digests are unchanged. No budget amendment was made.

The 20 publication-usage diagnostics exactly match the prior receipt. Native validate exits 2 with declared rules UNKNOWN and no failures; full architecture report exits 0. The private receipt binds both artifacts and every UNKNOWN record by canonical digest. Historical human budget acceptances remain unchanged.

CI-ONLY VERIFICATION: current-fix full CI, external services and Windows are not independently established here. Build external includes remain unsupported, cross-descriptor memstore completeness remains UNKNOWN, and issue 281 cause remains UNKNOWN. This review does not prove native-client end-to-end behavior, full CE complex-reference acceptance or public installation. Root owns final CI and merge decisions.

Independent completion gate: exit 0, `Architecture completion: 0 violations; 311 assessed UNKNOWN records remain.` Log: `astra-completion-gate.log`.

The reviewed source bytes are committed in `606781c68a3fb8cd6bca883a6770d1ba4faadf44`. Raw evidence is retained under `/private/tmp/datamimic-ce5-final-ci/`; the prior include review records the accepted six-call delta.
