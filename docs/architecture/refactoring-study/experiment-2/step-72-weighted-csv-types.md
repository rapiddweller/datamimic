# Step 72: type weighted CSV rows

Added three return annotations at the existing IO owners: the weighted
reader returns float weights and string-valued row maps; the selector returns
one row; construction returns `None`. Production bodies are unchanged.
Astra approved the scoped code and [exact measurement decision](amendment-78.md).
This is verified typing progress, not complete step/architecture acceptance.

The slice starts from the dirty `f134fcc7` working baseline. Source digest
changes from `787567dc668fcb1210503ae2080c7834216948c56247a144a76ed4f802247caf`
to `72130b74c2e8062832a84b82456d650c740245b6b783fedc6dd89c88cb20b963`.
Earlier dirty source/contract changes are not part of this checkpoint.
The protocol cross-reference is also omitted because that file contains
earlier unfinished hunks; integrating that reference remains open.

Independent QA passed eight behavioral checks on the pinned BEFORE source
and nine checks on current source. The added selector-annotation assertion
fails on BEFORE as intended. Reader-annotation RED is an explicit missing-type
assertion; current reader tests pass. A single-selectable-row RNG test was
replaced with a literal baseline sequence over three positive-weight rows.

LOCAL VERIFIED: the exact six-file checkpoint, applied to clean `f134fcc7`,
passes 1,493 Unit tests, with 11 skipped, 1 xfailed and two Pydantic warnings;
Make Ruff and full-package MyPy (491 files) pass. Its final focused
reader/selector tests, unchanged weighted integration descriptors, functional
capture and seeded DSL scenarios also pass: 46 tests. The broader dirty
integration checkout separately passed 1,500 Unit tests, recursive definition
(5 tests) and pinned Pylint cyclic-import checks; it contains earlier changes
that this checkpoint does not publish.

Public ArchKeel 0.8.1 measures 112 violations and 158 counted UNKNOWN
positions (233 raw UNKNOWN records). Only the reader return changed from
UNKNOWN to violation. Typing positions remain 145 against budget 143;
cycle edges remain 2. No contract/baseline changed in this slice. Final
strict architecture acceptance remains FAIL, not PASS.

The isolated six-file checkpoint measures 121 violations and 160 counted
UNKNOWN positions under public 0.8.1, with 145 typing positions and 2 cycle
edges. Its higher totals are not a regression from the dirty integration
checkout: earlier source/contract changes are deliberately absent. Both
snapshots remain gate-red.

The fresh HTML/JSON report uses hierarchy candidate
`0.8.2.dev27+g5d1506f11`, not a released 0.8.2. Its JSON is byte-identical
to the public 0.8.1 observation. Report visual approval remains separate.

The 930 tracked XML inventory has identical BEFORE/current byte hashes;
this is not runtime proof. Full serial BEFORE/AFTER no-service captures
completed with equal status totals: 383 CAPTURED, 70 EXPECTED-ERROR,
16 NOT-A-DESCRIPTOR, 77 UNRUNNABLE and 384 UNVERIFIED. All four projection
payloads/hashes are identical, and all 109 captured seeded result/output
digests match. No descriptor status changed.

The unchanged comparator still rejects the pair: 478 differences, comprising
470 incomplete-evidence records and eight unseeded projection differences.
Equal current capability projections are rejected by its historical
version/wording bridge. The functional weighted sample is null-only and
remains unverified by that comparator despite its passing explicit functional
assertions. No full-corpus equivalence is claimed; unchanged-source repeats
of the eight unseeded cases were checked separately, without exclusions.
Two BEFORE repeats reproduce condition, JSON-chunk, memstore-count and XML
template variation. City remains null-only in the repeats; the `multi_xml`
AFTER difference does not recur on BEFORE. Those gaps are not waived.
The capability bridge also rejects the valid BEFORE projections against
themselves: current schema `4.3.1.dev246+dirty` differs from its hard-coded
historical `4.3.1.dev89+dirty` guard. This is a comparator false positive,
not changed capability content.
Service cases were not executed by this oracle. Root verified healthy CE
Postgres/Mongo containers; sandbox access denial is not an infrastructure
outage. An independent service-scope assessment identified 224 currently
service-classified descriptors, not the older approximate count.

The BEFORE clone's reader test briefly contained the annotation
assertion for RED and was restored byte-identically; production, XML and
oracle code were untouched. That test is not executed by the descriptor
oracle; historical overlap timing is unknown. Do not describe the whole
clone as immutable throughout.

CI-ONLY VERIFICATION: pending checkpoint publication. This log records local
evidence, not a remote CI pass or complete architecture acceptance.
