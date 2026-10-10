# Step 98: list behavior evidence

Base `3d3928bc`, published ArchKeel 0.8.5. Astra chose a test-only step before
more boundary allowances. Two list integration tests are currently smoke
tests. The generic oracle cannot represent their heterogeneous item counts.
Keep its three UNVERIFIED cases and full comparator failure unchanged.

## Independent ownership

1. Luna QA owns `tests_ce/unit_tests/test_task/test_structured_list_tasks.py`
   and ignored mutation/coverage evidence. Trace real ListTask/ItemTask
   behavior independently. Test ordered heterogeneous items, field isolation,
   optional/false conditions, whole-list conversion and empty collections.
   Reuse existing context patterns; no new test framework or blanket mocks.
   Demonstrate that the old integration tests miss malformed captured data,
   then challenge the new assertions with count/order/field/leak/length faults.
2. Luna implementation owns only
   `tests_ce/integration_tests/test_list/test_list.py`. After root's baseline
   confirmation, enable existing capture and replace both smoke tests with
   structural assertions derived from the unchanged XML, not generated values.
   Two profiles: two ordered petList items, number 64 in the first; two pets
   with one inner record each in the second. Two array_child records: first
   item has the fixed name/filmography; second has ten integers. Assert exact
   fields so item contents cannot leak. Random strings/integers need correct
   types, not cross-run value equality. No duplicate converter assertions.
3. Root reviews tests and negative controls, compares unchanged source,
   descriptors, contracts and oracle, and requests Astra final review before
   commit/push to Draft PR274.

## Acceptance

Run new unit tests, both integration tests and existing converter/memstore
assertions; Make units/lint/full MyPy; existing architecture subchecks and
published report. Measure focused statement/branch coverage for ListTask and
ItemTask before/after using the same suite plus the new unit file. This is
not repository-wide coverage or the 90% goal.

No production, descriptor, oracle, contract, baseline, budget, skip, xfail or
gate edits. No architecture-count decrease is expected. New tests supplement
the three unresolved replay cases; they must not turn those cases into an
alternative PASS. Full DSL equivalence, broader coverage, EE and report
navigation remain open.
