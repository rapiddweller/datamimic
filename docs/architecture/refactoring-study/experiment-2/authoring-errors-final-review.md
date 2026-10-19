# CE Authoring and Errors final architecture review

**Accepted within the local architecture review scope. No remaining actionable finding.** Reviewer: Astra. This follow-up preserves the preceding whole-branch approval for unchanged paths and reviews the five-file delta from `8a8dc1baade090faaa42a2040d9a994ea2db88b1`. It does not authorize merge or assert native all-PASS.

## Current binding

- Source: `7b584450cc2473a516ec75d59a558e102dba9b8ccede61946a094971a20a3e0c`, scope `datamimic_ce/**/*.py`.
- Target: `8517a10b1fd874b2e66f7161044074d8ff649639a9f8e37e17f92c2456cc0d85`.
- Analyzer: `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f`; ArchKeel 4.0.1, Python 3.11.12.
- Canonical validation digest: `0805a19907a948bf130e89544f35da0a5328e3180fc0a3a5e7f676a6341a60f2`.
- Approved budgets remain exactly 1,425 unresolved calls and 178 typing positions. No policy or gate weakening accompanies this repair.

## Source review

`TimeSeriesConfig._parse_datetime` and `frozen_clock` now pass input directly to `datetime.fromisoformat`, available for UTC `Z` on the required Python >=3.11. The typed TimeSeries exception and cause remain. Frozen-clock naive-input UTC assignment and aware-input UTC conversion remain. Callers in GenerateStatement, acceptance projection and person API still use the same owner. The two deleted normalizations need no replacement abstraction. `typing_extensions` is retained for actual Python 3.11/Pydantic TypedDict and recursive-alias needs, not a restored 3.10 compatibility layer.

The snapshot-race fixture renames the original file outside the scanned workspace before writing its same-sized replacement, keeping the original inode allocated. It explicitly asserts distinct `(device, inode)` values. The production reader, containment rules, `ValueError` type and `changed before opening` expectation are unchanged. Existing independent negative controls reject both a disabled identity check and a check delayed until after reading; this correction does not merely permit a different failure.

The exact CI failure's cause remains UNKNOWN: no original stat pairs were captured and independent Linux probes did not reproduce it. The correction removes the fixture's unproven identity-change assumption. Existing metadata checks are not an atomic or immutable filesystem snapshot and are not presented as a sandbox.

The preceding whole-branch review remains applicable to unchanged application/ports/adapters, transient DM JSON and persisted XML, mandatory complete-capture acceptance, smoke/replay gates, resource ownership, migrated CLI/MCP, one-time legacy migration and portable Errors paths. Hash comparison against the previous wheel identifies exactly these two product-module changes. The old installed-wheel evidence therefore supports unchanged files, not an exact-byte installation claim for this new candidate.

## Native result and UNKNOWN assessment

Fresh coverage remains 534/534 full AST, zero violations and zero baseline additions/resolutions, with no validation failures. Rules remain **271 PASS and five UNKNOWN**. Native validation exit 2 retains the exact 20 `interface.usage_unknown` diagnostics; full completion reporting succeeds.

Call observation is 12,958 total: 9,539 resolved, 1,994 partially resolved and 1,425 unresolved. Independent decoded comparison finds exactly two removed partially resolved calls, `iso_datetime.replace` and `value.replace`, and no added semantic call. No unresolved call was promoted to resolved.

All 303 raw UNKNOWN records and all 20 diagnostics are structurally unchanged. The fresh receipt retains every UNKNOWN exactly once in 12 explicitly assessed groups: four API surfaces; 284 boundary positions (including real missing-annotation/broad-shape debt); seven DSL publication routes; six overlapping aggregates; one context-alias limit; one dynamic-call limit. All 20 publication-usage diagnostics retain their exact pointers, including repeated symbols at different publication routes. No record is dropped, reclassified as PASS or interpreted as permission to remove a public entry.

## Evidence boundary

**LOCAL VERIFIED independently:** connected five-file source review, two-file package delta, native identities and decoded call delta, complete raw UNKNOWN/diagnostic equality, unchanged policy, strict gate acceptance of 303 UNKNOWNs, and rejection of the stale prior receipt. No new collector or duplicate product suite was run by this reviewer.

**LOCAL VERIFIED through supplied evidence:** the same seven UTC/offset/naive scenarios passed before deletion; both full focused modules then passed 24 tests; two snapshot controls passed; the independent snapshot review's three-case positive/negative matrix confirms the strict expectation. These are scoped results, not a full-unit run.

**CI-ONLY VERIFICATION:** CI 39179520411 recorded 2,975 passes, one snapshot-fixture failure and 15 skips. It remains failed. The later local full-unit attempt was interrupted and is not counted as a pass. A new exact-head CE CI run, applicable Windows/service execution and merge decision remain with the parent/user.

Skipped: duplicate broad tests, collectors and EE audit. Residual risk is retained native uncertainty and outstanding final-head CI; no complete immutable-snapshot or whole-system correctness claim is made.

## Mongo capture test follow-up

The additional external-service CI failure was a false COMPLETE expectation for an uncounted Mongo source: the run recorded 184 passes, one failure and three skips. The corrected test now explicitly requires UNKNOWN, requested=None and observed=2 for that source, then uses ElementTree to add count=2 solely to a separate positive-control XML. The existing typed ObjectId equality, normal runtime, sampled public rendering and unchanged database readback assertions remain. It additionally compares the uncounted and counted captured rows. Production policy and receipt identities are unchanged; no row count is injected into user data or the persisted runtime descriptor.

Source review accepts this test-only correction. Reviewed live evidence from an ephemeral MongoDB 7.0.12 confirms UNKNOWN versus COMPLETE and preserves native ObjectIds, public rendering and database readback; all three bound production-file hashes match. This is supplied live probe evidence, not an independently rerun complete service suite. The CI workflow (.github/workflows/main.yml:627–628) declares mongo:7.0, so local 7.0.12 belongs to the same major/minor family; the exact CI image patch and host can differ. MongoDB 8.0.29 was only a discarded local startup attempt that refused the local kernel; no compatibility check was bypassed. The failed CI result remains failed, and final exact-head CI remains required.
