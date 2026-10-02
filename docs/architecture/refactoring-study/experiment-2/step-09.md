# Step 09: domain IDs and target-state boundary

Amendments 15 and 16 govern this slice. Fourteen fields declared as unique IDs in
the existing entity schemas now claim values from one registry per CE engine run.
Direct service batches use a service-local registry. The original candidate and
RNG sequence are unchanged unless that candidate collides; fallback stays in
the field's existing format and is deterministic. Nested insurance company and
product IDs use the same run registry. CE runs an affected DSL generate serially
so page and worker boundaries cannot split the registry.

This is not a target-database uniqueness lookup. An existing target conflict
fails on insert; explicit SQL upsert matches the primary key, not a secondary
unique index. No ID is silently rekeyed against target state. No XML, target
architecture, baseline budget, or ArchKeel rule changed.

## Verification

- Focused API, constructor, runtime, and SQLite target tests: 51 passed. A
  forced repeated Patient candidate across two pages yields four distinct IDs
  with both serial and requested two-worker settings. SQLite tests cover clean
  replay, insert conflict, PK upsert, and secondary-unique conflict. The
  finite one-value ID format raises an exhaustion error.
- Serial non-external CE suites on the final production revision: 3,782 passed,
  28 skipped. Two Pydantic serialization warnings remain. The stronger
  cross-page and memstore assertions were rerun separately after their edits.
- `make lint`, full-package `make typecheck` (475 files), and pinned ArchKeel
  0.6.1 pass. ArchKeel reports 0 violations, 0 material unknown positions,
  171 cycle edges, 1,279 unresolved calls, and 144 typing positions: no
  increase against the frozen budgets. The new shared entity-constructor
  parser removed two false unresolved string-method positions.
- The full oracle inventoried 930 unchanged XMLs. Status: 454 captured,
  62 expected errors, 16 non-descriptors, 76 unrunnable, 322 unverified.
  Frozen versus candidate has one difference:
  `test_memstore_sum_and_count.xml` drew 21 versus 11 unseeded rows, both
  within the descriptor's 9–21 range. One isolated frozen run showed
  `len(te) == totalCount == teCount == 13`; the strengthened candidate test
  checks the same invariant and passed three isolated runs. The previously
  lost `test_data_type.xml` result was captured and matched frozen in this
  run. Three selected seeded descriptors match their prechange result and
  output digests exactly; one selected unseeded entity descriptor matches
  count and shape. Authoring and capability projections remain hash-identical.

## Remaining boundary

The 322 oracle-unverified cases, including external-service descriptors,
remain unverified; this slice alone does not make Experiment 2 merge-ready.
The existing unseeded comparator also treats `null`/`unknown` as wildcards
and does not inspect every exported file's content, so its green comparisons
are bounded evidence, not universal structural proof.
Existing generic `<key generator="…" unique="true">` can still repeat at a
page seam because its task-local seen-set is rebuilt per page. That separate
DSL defect has a reproducible two-page probe and is not claimed fixed here.
