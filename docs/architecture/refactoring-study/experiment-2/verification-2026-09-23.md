# Experiment 2 verification, 2026-09-23

Updated 2026-09-24. This report separates declared structural acceptance from
behavioral evidence and delivery gates.

## State

- CE branch: `experiment/target-architecture-v2`; last production-package change
  `5c37e158`. Later commits change tests, the experiment oracle, and evidence only.
- The final checker is published [ArchKeel 0.6.1](https://github.com/rapiddweller/archkeel/releases/tag/0.6.1),
  tag `6f865167`, analyzer `0.47.0`. Its tag workflow passed build and PyPI
  publish; a fresh isolated PyPI install reports `archkeel 0.6.1`. The frozen
  0.6.0 tag remains the Step-0 control; it cannot parse Amendment 11's
  `allowed_positions` field.
- The contract scan is complete (474/474 files), with 0 violations, 0 unknown
  positions, and `declared_rules=PASS`. The violation baseline is empty. Twenty
  neutral raw UNKNOWN records remain (Amendment 11).
- The 0.6.1 `validate --against` check passes against frozen Step 0: no new or
  resolved baseline violations. The exact current measurement budgets are 1,283
  unresolved calls (narrowed from 1,288), 171 cycle edges, 144 typing positions,
  and 3 untyped private accesses. `archkeel report` was regenerated with the
  published package; the generated JSON/HTML stays outside the repository.
- Internal cycle debt remains: 7 SCCs (6 module, 1 package), covering 171 cycle
  edges. The largest module SCCs contain 28 DSL parser modules and 23 runtime
  modules. The declared component graph has no cycle; this is not a claim that
  package/module cycles are gone.

## DSL oracle

The full inventory has 930 XML files. Their raw content is byte-for-byte
unchanged from frozen Step 0, including demos relocated from
`datamimic_ce/demos/` to `datamimic_ce/resources/demos/`: both checkouts have
930 files and the same 930 content hashes (898 unique). Four comment-only
edits made during the refactor were reverted for this constraint. The earlier
comparison snapshot at `a2e227ab` has SHA-256
`96f796371002fc4059e1b7882b855c7e9a5e50d42364a0291a838bf3576112ac`.
Both frozen Step-0 comparisons report 0 differences; all four authoring projections
match. Snapshot G has one tolerated unseeded shape variance in
`tests_ce/integration_tests/test_entity/patient.xml`: `de_patients.allergies`
is `array<unknown>` there and `array<str>` in the final run. Snapshot H also
records `array<str>`.

A fresh full pair with the stricter error comparator used frozen `a219163e`
and candidate `de1d5e6a`, the same verifier hash
`4e34e98c35f8a20a53854b2944bfa24cfdfc1ced8d0fa41ef90e2f44424e1f1f`,
and asserted the imported checkout in parent and child processes. It reports
930 compared, **0 hard differences**, and four tolerated descriptor-path
variances. Two are optional unseeded shapes: city `population` (`null`/`int`)
and order `coupon_code` fields (`null`/`str`). Frozen unchanged code itself
produced both city shapes in three repeats and both order coupon shapes in 50
repeats (49 `str`/`str`, one `null`/`null`). The other two variances are only
member ordering in the expected-error allowed-attribute set. Snapshot SHA-256:
frozen `c6bc1ac6deb6eb360d09ec9a2e0333c148ac584fb238221e3e86d9837cff571d`,
candidate `d39f7641b2d586c4726388b562f1071a63ba3de989d765ba9a3b987379da756e`.

The capture covers 454 successful descriptors, 62 expected errors, 16 files that
are not descriptors, and 76 unchanged unrunnable outcomes. Another 322 are
unverified by this oracle: 273 service descriptors, 40 standalone authoring
fixtures, and 9 dependent fixtures. The later test/oracle/evidence commits change
no production or XML descriptor files.

The comparator now checks exception class and normalized detail for expected
errors. It sorts only the known unordered allowed-attribute set in two DSL
diagnostics; unrelated text, missing detail, and changed exception types fail.
Two same-commit repeat pairs match on all 63 and 62 common expected-error cases
after this normalization. The fresh full pair above also has no hard difference
under the stricter comparator.

Three of the 9 XLSX-dependent descriptors were compared separately against the
frozen Step-0 checkout with the same 12-row workbook fixture. The full captured
rows match byte-for-byte: `read_random_seeded.xml` (12), `read_paged_ordered.xml`
(12), and `read_cumulated_seeded.xml` (200). Both canonical capture files have
SHA-256 `6d206b67c795442d93ef398a2ef25636ee036e3193d4eecf2b4a1b5473abb7ac`.
The runner asserted the imported CE checkout in both processes. The automated
inventory still skips all 9. The remaining six were also compared separately:
`read_complex_cyclic.xml` (10 rows), `read_cyclic_paged.xml` (26), `read_xyz.xml`
(2), and `xlsx_read.xml` (2) have exact captured-row hashes on both checkouts.
`read_count_only.xml` matches for empty, header-only, blank-header, and malformed
workbooks, including the error type and detail. `read_random_unseeded.xml` is
intentionally non-identical in order; both versions produce valid 12-row
permutations with the same row shape. Fixture creation, Python 3.11.12, openpyxl
3.1.5, and imported CE checkout were controlled. The oracle now uses only XML
and filesystem facts to classify absent XLSX sources. It exempts a workbook
generated in the same descriptor, but does not infer fixture creation from
sibling Python tests. This is a conservative skip hint, not proof that arbitrary
test setup executes.

| Additional exact XLSX capture | Rows | SHA-256 on both checkouts |
|---|---:|---|
| `read_complex_cyclic.xml` | 10 | `69f94eba6ea8ffa0e1cf63ff84bff5a76a87e842e63e39d6a92f6b896ee0930f` |
| `read_cyclic_paged.xml` | 26 | `4195b2f5d5d1a706620e3ae812b1edb68962ad1271c7c07c1f4fb302820f6364` |
| `read_xyz.xml` | 2 | `3748ba1f3bad597a9a8150eeca63f0184a3c050f49976dcd5ddfc32bfb7f8d91` |
| `xlsx_read.xml` | 2 | `6a3d170bdaacb3d4cbd572d26aac2625d749e4d199b6f96e95b1c3bb86c133d3` |

All 43 tracked XML authoring fixtures yield identical lint results between Step 0
and HEAD: 18 clean, 25 with the same complete diagnostics after removing only
the checkout-specific absolute file prefix. The generic runtime oracle skips 40
authoring-only inputs; two more are also service-classified, and one is not a
descriptor. This lint comparison does not prove every dry-run/export outcome.
The automated oracle still reports 313 skips beyond the nine XLSX inputs:
273 service-classified and 40 authoring-only inputs. Separate comparisons below
cover a subset of these skips without changing the oracle's categories.

## Serial tests

| Suite | Result |
|---|---|
| Unit | 1,167 passed, 11 skipped |
| API, before hygiene | 355 passed, 1 skipped, 1 random-collision failure |
| API, after test-only hygiene commit | 333 passed, 1 skipped |
| Factory | 4 passed |
| Functional | 132 passed |
| Integration | 544 passed, 2 skipped; one sandbox socket failure passed with loopback access |
| Architecture | 1,542 passed, 14 skipped |
| External, OrbStack | 152 passed, 10 skipped, 6 environment failures |

The API failure was a valid age collision. Ten isolated repeats produced nine
passes and one failure. Commit `9d5e9c5c` removes 23 tests that asserted
unpromised random inequality, including this case; no runtime behavior changed.
This fixes one flaky test pattern, not a repository-wide duplication audit or
unified CE test-utility design.

The deletion also exposes a pre-existing contract ambiguity: 11 removed tests
compared IDs described as “Unique identifier” in domain schemas. None of their
`generate_batch()` implementations enforces cross-row uniqueness; they draw
finite random suffixes or UUIDs with no collision tracking. A fixed-seed batch
test would only prove one sample. Whether uniqueness must be guaranteed or the
descriptions should be narrowed is a separate API decision, not an oracle fix.

The six external failures are MSSQL/Oracle tests configured for local ports
1433/1521. OrbStack exposes 41433/41521. A temporary port-only rerun reached
both servers, then failed on the existing MSSQL credentials and Oracle service
name. The temporary config edits were reverted. Step 08c17 records six passes
with fully matched local fixture settings. The port-only run did not prove those
six against today's service configuration.

The same six tests then passed serially (`6 passed` in 44.45 s) against fresh,
disposable MSSQL 2025 and Oracle Free 23 containers, using copied fixture trees
and matching local configs. Both containers and copied fixtures were removed;
the shared Platform databases were not touched. This proves the six paths under
that isolated environment, not one green run of the entire external suite.

The 273 service-classified skipped XMLs are not 273 known database programs:
213 live under `external_service_tests`, 60 are client-tagged demos, and 116 of
the 273 have no direct database/MongoDB/Kafka/object-storage element. Test-owner
mapping divides those 116 into 80 local-only cases and 36 cases with indirect
service dependencies through an owning setup. The oracle skips both groups by
suite policy; neither group is counted as runtime-equivalent without a separate
Step-0 comparison.

The other 157 service-classified inputs declare a DB or Mongo client: 154 real
service-backed runtime descriptors, two authoring-only fixtures, and one
`dbms=db2` negative fixture whose test expects validation failure; DB2 must not
be provisioned. Of the 154 service-backed descriptors, 62 use SQLite and can
be isolated without a container. Backend memberships overlap for five
PostgreSQL+MongoDB descriptors; the other backends are PostgreSQL, MongoDB,
MySQL, MSSQL, and Oracle. Existing `local.env.properties` files can point at
shared databases, and owner setup scripts drop tables or modify fixed MongoDB
collections. Staged XML alone is not isolation: every service comparison needs
an asserted disposable endpoint and database before execution. The existing
MySQL pytest fixture restarts and stops `mysql-local`, so it must not run against
the user's stack.

The first local-only case, `test_variable_file_distribution_matrix.xml`, now has
an isolated Step-0 comparison. Both checkouts use the same three copied CSV/JSON
inputs and produce identical seeded capture digests: result
`20cc7f95b9ef6a2e7558f4385aace4b2a6b9aa7b389b180bb9277be68fb0e3a3`,
no exported files. The runner asserted the imported checkout in each process.
Thirteen further standalone local-only source-cyclic descriptors also execute
successfully on both checkouts with identical normalized oracle records, XML,
and input fixture hashes. They are unseeded: the oracle compares outcome,
recorded counts, shape, and output names, not generated row values. Dynamic
counts are labeled `dynamic` rather than measured. This is execution
and shape parity for 13 cases, not exact dataset parity.

Another ten local-only variable/storage descriptors have matching Step-0
capture records from isolated copies: six successful outcomes and four matching
`ValueError`s. One failing input (`test_memstore_access.xml`) is already marked
skipped by its owning pytest test; matching its failure is not proof that it
works. Two successful storage descriptors are seeded and have exact captured
result/output digests; the other eight are unseeded and prove only the oracle's
normalized result/error contract. The ten XMLs and their input CSVs are
byte-identical. The remaining local-only demo cases are assessed next.

Fourteen local-only `g-entity` demo XMLs were checked next. Eleven aggregate or
valid leaves succeeded on both revisions with identical unseeded normalized
records. Three leaves outside the aggregate fail on both revisions because
`<generate>` rejects child `<attribute>`; their diagnostic member order is
nondeterministic, so raw message hashes differ while exception type and
diagnostic members match. These are failure-parity cases, not successful DSL
executions. Forty-two local-only demo cases remain without a separate
comparison. Of the other 193, the six SQLite comparisons below are now covered;
187 remain. Those 187 comprise 148 directly service-backed runtime descriptors,
36 aggregate-owned fragments, two authoring-only fixtures, and one
expected-invalid DBMS fixture.

One of the 62 SQLite descriptors, `sqlite_seeded.xml`, has since passed an exact
Step-0 comparison. It declares `rngSeed=42` and inline SQLite settings; both
revisions used separate temporary databases with an empty staged config to
prevent fallback to shared settings. The captured result digest matches
(`d02bed68b2e4e3c182fe8a74cac2a908e57bbd722b4a90edb640f972ff3d65bb`),
as does the SQLite file hash
(`c15858b418b2aa83317f0f764e95dfcaf040213602a5ec1c440333981e682c64`).
Each temp database contains the same 12 IDs; no shared service was used.

Five more seeded SQLite descriptors passed exact Step-0 comparison in separate
temporary stages: binary export, composite reference, variable distribution,
nested insert order, and ordered reference. The combined canonical fixture,
capture, normalized export, and SQLite content evidence has SHA-256
`be06f99b9e0a6e58bdc783a3b339a8aa8f542cd3b95d049c6318847a3fa6efcd`.
All DB and output paths stayed inside each stage. The XLSX export differs in
raw OOXML timestamp/task metadata; its normalized content matches, as do the
CSV/JSON bytes. Fifty-six SQLite-using direct descriptors remain without a
separate comparison.

Ruff and full-package MyPy pass. `make lint` fails at Pylint with exit 30. With
Pylint 3.3.7, frozen code and experiment have the same 24 error-severity
findings by symbol and message. Total findings are 3,509 versus 3,707 in the
latest paired run, mainly 212 additional convention messages. Historical
lint debt is not hidden by changing the gate.

ArchKeel currently scans only `datamimic_ce` (`archkeel.toml`), not `tests_ce`.
Its contract therefore does not enforce test placement or test dependencies.
Duplicate assertions and descriptor/result equivalence are behavioral questions;
the experiment checks them with the test suite and frozen oracle, not by treating
zero ArchKeel violations as test-quality proof. The separate test-namespace
governance gap is tracked in [ArchKeel #143](https://github.com/rapiddweller/archkeel/issues/143).

## Verdicts after Amendment 12

- **Structure reached, locally:** exact layout and component rules pass with complete
  coverage, an empty violation list, zero material unknown positions, and no budget rise.
  This is checked with the publicly installed ArchKeel 0.6.1 package, not a local
  candidate. It does not prove behavior or test quality.
- **Behavior preserved for the comparable oracle set:** both frozen comparisons have zero
  differences. All 9 XLSX-dependent cases have controlled parity evidence; all
  43 authoring XML fixtures have identical lint results. Of 273
  service-classified skips, nine have exact seeded runtime parity and 35 more
  have normalized outcome/shape/error parity only. The remaining 229 lack a
  separate Step-0 run; the unseeded 35 also lack exact row comparison. An unqualified
  all-descriptors claim is not supported.
- **Delivery not ready:** `make lint` remains red, the complete external-service
  suite has not passed in one isolated run, and remote CE CI has not run. No CE merge or
  release is justified by the structural verdict alone.
