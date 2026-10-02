# Step 0 descriptor oracle

The oracle inventories every XML file under `demos/` and `tests_ce/`; no descriptor is removed as
flaky. Two independent Step-0 runs compared 930 files with 0 differences and 1 tolerated
optional-shape variance.

## Stable Step-0 evidence

- statuses: 454 captured, 62 expected errors, 16 non-descriptors, 76 unrunnable, 322 unverified;
- Step-0 snapshots:
  - `bcb06fb270747f91a23557e590875f5d29e5126d5d9bcbfc9abc70504390ecca`;
  - `1b4217ca6a69a90d80b379f01e7480e61b163105bb6fafe1528337f06b700f20`;
- seeded cases compare exact captured-result and normalized-output digests;
- unseeded cases compare outcome, product names, static row counts, output filenames, and value
  shapes; `null` is treated as an unobserved optional value rather than a conflicting concrete type;
- capability, compiler, authoring-reference, and scaffold-reference projections are hashed and
  compared exactly.

The 322 unverified files are 273 external-service descriptors, 40 authoring fixtures, and 9
test-fixture-dependent cases. Podman was unavailable, so no service was started and these cases are
not presented as runtime proof.

The 76 unrunnable files are standalone fragments or negative cases: 24 DSL/invariant failures, 16
unbound setup or script names, 8 missing setup-state keys, 7 missing targets or client
registrations, 7 selectors needing a database client, 7 unsupported entities, 5 seeded-entropy
rejections, 1 missing scripted source field, and 1 multiprocessing/global-import limitation. None
failed because an adjacent fixture file was missing.

That nullable-shape rule is evidence-based. Twelve unchanged Step-0 captures of
`test_entity_city.xml` produced `de_cities.population=null` eleven times and `int` once. The two
captures differed only in that sampled field type; their hashes are
`bd8e906d6233c4762bfe1d8ad31ff1b19eda7c8fbf0c67c64d5064f0b08682af` and
`d7533c6aa5ce8c93396f8b6d786a51b16df1259f2b68bd58c2b4abbcb6af564c`.

The harness is `script/architecture_study/verify_step0.py`; comparison is
`script/architecture_study/compare_step0.py`. Full snapshots stay outside the repository under
`/private/tmp`.
