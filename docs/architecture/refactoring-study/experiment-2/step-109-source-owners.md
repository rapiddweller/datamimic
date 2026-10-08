# Step 109: dissolve the mixed source registry

Base: `854cfaa6`. Astra confirms existing owners: file decoding in
`io/files/readers.py`, query-count failure translation in `io/clients/operations.py`,
and routing/window selection in `io/data_sources/router.py`. Delete the stateless
registry and its five duplicated window wrappers; no new layer or public grant.
The recursive target records the split; historical structure reviews stay unchanged.

Preserve format dispatch, cache/row identity, order, separators, copy policy,
offsets, partial bounds, `None` normalization, errors and log levels. DbUnit stays
offset-only. The generator-cache split is deferred: DSL names can collide with
reference-cycle keys, and worker/scripting identity needs separate proof.

Independent Luna implementation and QA; root corrects bool coercion, a historical
record deletion and lost routing assertions before acceptance.
Independent Astra final review finds no remaining issue in this slice and reruns
the 114 focused controls successfully.

LOCAL VERIFIED: **2,250 unit tests passed, 11 skipped, one existing xfail**;
42 file/SQLite integration tests; 114 focused controls; 24 recursive-target and
IO-boundary tests; source/changed-test Ruff; full MyPy (491 files); pinned Pylint.
Two existing Pydantic serializer warnings remain.

Frozen recorder: 930 XML inputs inventoried, 13 selected. Ten captures
(five seeded, five unseeded) and one expected error compare equivalent. The
strict comparator still exits 1 for two pre-existing incomplete captures:
`cascade_unseeded.xml` and `test_import_xml.xml`. All four projections match
before/after; all descriptor, intent and oracle hashes remain unchanged.
This is bounded evidence, not full DSL acceptance.

Published **ArchKeel 1.0.0** parses 491/491 files, AST coverage 100%.
Contract remains **FAIL: 91 violations, 202 UNKNOWN positions**, baseline-new 60,
resolved 0, two measured cycle edges. No baseline, allowance or gate is weakened.
Full service/descriptor and Actual/Target/Diff navigation acceptance remain open.

CI-ONLY VERIFICATION: no passing remote result claimed.
