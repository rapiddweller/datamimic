# Step 42: typed transition grammar

`<transition>` has one typed model used by the state-machine parser and the
authoring schema index. Its module and responsibility are declared in the
nested DSL-model target contract and the physical move map.

Three state-machine descriptors matched the previous CE capture: two seeded
result/output digests and one unseeded structural record. The authoring
projection differs only at `elements.transition`, as recorded in the dated
amendment. This step does not claim full descriptor or target-architecture
completion.

Local gates: 1,471 unit tests passed (11 skipped, 1 xfailed); 56 focused tests
and 9 architecture-definition tests passed; Ruff and full-package MyPy passed.
ArchKeel observed all 490 Python files, with the same 123 violations, 194
UNKNOWN positions and 93 new-baseline findings as before this step. CI and
the full descriptor corpus were not run for this slice.
