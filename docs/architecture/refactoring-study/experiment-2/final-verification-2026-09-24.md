# Experiment 2: final verification review, 2026-09-24

## Verdict

**Declared structure reached locally; behavioral equivalence not fully proven;
not merge-ready.** This is an evidence boundary, not a claim of a known DSL
regression. A draft PR is possible after push, but it must carry these gaps.

Frozen control: `development` at `a219163e533d661bcc7bda0faa5ecc77909ab5aa`.
Candidate: `experiment/target-architecture-v2` at `5ac964d1a14a864d35dc7c5ef8b3d3d6a189a3a4`
before this report. Both test runs used fresh `git archive` copies and the same
CE virtual environment, with `PYTHONPATH` asserted to resolve into each copy.
No user-owned checkout or shared service database was modified by these runs.
The strict descriptor snapshots are
`/private/tmp/dm-exp2-strict-serial.8AZRUg/{frozen,target}.json`
(SHA-256 `49d2c98f...e845a2b7` / `c451c4d9...2ecc9f`).
JUnit evidence for the six paired suites is under
`/private/tmp/dm-ce-final-{old,new}-{unit,api,factory,functional,integration,arch}.xml`.

## Old versus new tests

All suites below ran serially (`-n 0`, no automatic reruns) on both revisions.
This avoids hiding failures behind xdist scheduling or retry policy.

| Suite | Frozen | Candidate | Interpretation |
|---|---:|---:|---|
| Unit | 1,153 pass, 11 skip | 1,173 pass, 11 skip | New boundary/oracle tests; removed obsolete parser and duplicate tests. |
| API | 356 pass, 1 skip | 333 pass, 1 skip | 23 tests asserting unpromised inequality of random entities removed. |
| Factory | 4 pass | 4 pass | Same cases. |
| Functional | 131 pass | 132 pass | One CLI-init case added. |
| Integration | 544 pass, 2 skip, 1 sandbox failure | 544 pass, 2 skip, 1 sandbox failure | Same 547 cases; 12 parametrized case names were consolidated. |
| Architecture tests | 1,476 pass, 14 skip | 1,542 pass, 14 skip | File-parametrized cases reflect the moved package layout. |

The integration failure is `test_cli_sse_exact_tools_with_api_key`: the sandbox
rejects `bind(127.0.0.1, 0)` before CE code is exercised. The exact test then
passed separately on both revisions with loopback access (1/1 each). Thus the
effective integration evidence is 545 passing cases and 2 skips per revision,
but there was no single green full-suite command in the restricted sandbox.

`tests_ce/external_service_tests/` was **not rerun as a full old/new pair** in
this review. It includes PostgreSQL, MongoDB, MySQL, MSSQL, and Oracle paths;
the running OrbStack containers belong to other projects or use shared data.
Earlier target-only execution recorded 152 pass, 10 skip, 6 configuration
failures. The six later passed against disposable MSSQL/Oracle containers, but
that is not a complete old/new suite comparison. Shared endpoints must not be
used as a shortcut.

## Descriptor inventory and equivalence

- The 930 tracked XML files have the same bytes at frozen Step 0 and candidate
  (898 unique hashes; 104 were moved with 100% rename identity). No descriptor
  result was intentionally changed. The strict full-run snapshots used frozen
  `a219163e` and target `f312a455`; since then only
  `tests_ce/unit_tests/test_architecture_study_oracle.py` changed under
  `datamimic_ce`, `tests_ce`, or `*.xml`. Thus the snapshot covers the current
  production and descriptor revision, not the newest test-only commit.
- Of 196 root-seeded descriptors in the inventory, 88 were successfully
  captured in each full run. Their normalized captured rows and exported
  content digests match exactly. The other root-seeded paths are not silently
  counted as successful exact-output proofs; they have their recorded error,
  unrunnable, or unverified status. Nine XLSX-dependent paths were compared
  separately with controlled workbooks; OOXML timestamps are normalized.
- The generic oracle captured 366 unseeded paths on frozen Step 0 and 365 on
  target. It also recorded 62 expected errors, 16 non-descriptors, and 322
  unverified paths on each side. Its strict comparator returns **2 differences**:
  `test_data_type.xml` lost a result marker on one successful target full run,
  though three isolated reruns per revision captured the same 50 rows; and
  `test_memstore_sum_and_count.xml` returned different unseeded `te` counts
  (21 versus 17). The frozen program itself produced 15, 17, and 17 in repeat
  runs; the target produced 21, 13, and 13. The owning test checks the valid
  9–21 range and `teCount == totalCount`. Amendment 13 also requires checking
  `len(te)` against those values within each run.
- The two differences are not established regressions, but they are not
  resolved by the current automated gate. More importantly, the comparator
  accepts `unknown` and `null` as wildcards (`unknown -> object` and
  `null -> int` both return true). The shape capture unions fields across rows
  without recording presence, and for 94 unseeded captured descriptors it
  compares exported filenames but not output schema/content. Therefore a
  zero-difference result under this comparator would **not** prove structural
  parity for every unseeded descriptor.
- The 322 generic skips are 273 service-classified, 40 authoring-only, and 9
  XLSX-dependent paths. All 43 tracked XML authoring fixtures have identical
  lint results; all 9 XLSX-dependent paths have separate controlled comparisons.
  The strict service ledger binds only 25 of 273 service paths to exact
  path-level evidence (2 exact seeded, 8 matching errors, 15 normalized
  unseeded); 248 remain `UNVERIFIED`. Older aggregate claims of 100 paired
  service paths cannot be reconstructed per descriptor, so they do not close
  this gap. The 200,000-row SQLite page-process descriptor did run on both
  revisions: both produced 100,000 customer and 100,000 user rows with matching
  schema and foreign-key invariants; unseeded DB bytes differ.
- Authoring schema, reference, capability, compiler, lint, and transport
  projections matched in the frozen comparison. Public CLI/Python entry points
  are covered by the current functional and boundary tests, not by an external
  consumer upgrade test.

## Architecture and non-descriptor tests

`make architecture-check` with released ArchKeel 0.6.1 passes on the current
candidate: 474/474 files read and parsed, 0 violations, 0 material unknown
positions, empty violation baseline, `declared_rules=PASS`. The exact root
allow-list and acyclic component graph are enforced. This is a meaningful
improvement over the original crowded root and implicit crossings, but not a
claim of a cycle-free implementation: 7 internal SCCs / 171 cycle edges,
1,283 unresolved calls, 144 typing positions, and 3 untyped private accesses
remain under non-increasing measurement budgets.

The non-descriptor test organization is serviceable, not finished:

- `unit_tests/` mostly probes modules and typed public boundaries directly;
  `api_tests/` probes generated domain objects; `factory_tests/` has four
  focused cases. `functional_tests/` covers CLI/generator flows, while
  `integration_tests/` owns descriptor execution. The categories are human
  convention, not an enforced dependency/test-placement architecture.
- `unit_tests/` is not synonymous with “no descriptor”: authoring linter tests
  intentionally use XML fixtures. The root `conftest.py` is now small but
  still mutates `sys.path`. The XLSX integration fixture is function-scoped;
  other tests still manage module-local output directories themselves. We
  have not proved xdist isolation repository-wide.
- Test hygiene improved narrowly: 23 probabilistic inequality assertions
  removed, two duplicate authoring tests removed, the shared XLSX race fixed,
  and 12 near-duplicate unique-matrix cases merged into one parametrized test.
  There is no justified universal test-helper layer yet. Reuse the existing
  `DataMimicTest` and `tmp_path` where they actually remove repeated setup.
- The surviving `bank.name == bank.name`-style checks are **not tautologies**:
  `@property_cache` generates a value on first access and must retain it on
  second access. They test caching, although explicit naming could be clearer.
- ArchKeel scans `datamimic_ce`, not `tests_ce`. It cannot currently prove
  test placement, fixture isolation, duplicate behavior, or descriptor parity.
  ArchKeel #143 tracks test-namespace governance; a rule should enforce only
  test facts that are statically decidable, with runtime behavior left to tests.

## Delivery gates and decisions

LOCAL VERIFIED: Ruff passes; full-package MyPy passes on 474 files; ArchKeel
0.6.1 passes as above. `make lint` fails at Pylint on **both** revisions
(exit 30; frozen score 8.18, candidate 8.13 under this local setup). This is
pre-existing gate debt, but the lower candidate score is not a lint no-regression
proof and `make check` is not green. The serial suite results are
listed above. No full isolated external-service pair or fully sound unseeded
structure oracle has passed.

CI-ONLY VERIFICATION: no current-HEAD remote CE pipeline, PR checks, or merge
test has been verified. The branch has no configured upstream. A draft PR can
expose this evidence, but it must not be presented as merge-ready.

Before merge:

1. Make the oracle fail closed on `unknown`/missing capture; record field
   presence/nullability and exported schema, then check fixed counts and
   descriptor-defined dynamic-count invariants. Re-run the full 930-path pair.
2. Resolve the result-marker miss and create a path-addressable old/new ledger
   for the 248 remaining service paths, using disposable OrbStack/Docker
   endpoints and copied fixtures. Keep expected failures distinct from passes.
3. Decide the Pylint debt policy without silently weakening `make lint`:
   either pay it down or explicitly baseline old findings and block new ones.
   Run the chosen gate and the full CI matrix on the pushed branch.
4. Review removed API tests against the product contract. Alex needs to decide
   whether documented “Unique identifier” means guaranteed cross-row
   uniqueness; current random generators do not enforce that guarantee.

No further architecture sweep is justified by this evidence. The remaining
work is test/proof completion and one product-contract decision.

## Gate update, 2026-09-24

Amendment 14 supersedes the Pylint decision in item 3 above. Pylint was not a
declared dependency or CI gate; `make lint` now runs Ruff only. Two uncalled CSV
and JSON exporter reset overrides with invalid `super()` calls were removed.
The revised `make lint`, full-package MyPy, the unit gate (1,173 passed,
11 skipped), focused exporter tests (26), and pinned ArchKeel 0.6.1 passed
locally. ArchKeel reports 0 violations, 0 unknown
positions, and no new or resolved baseline findings after narrowing the
`calls_unresolved` budget to 1,279. The historical comparison and all other
open acceptance items above remain unchanged. `make check` and remote CI have
not been rerun on this update.
