# Experiment 2 verification, 2026-09-23

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

The full inventory has 930 XML files. The final snapshot at `a2e227ab` has SHA-256
`96f796371002fc4059e1b7882b855c7e9a5e50d42364a0291a838bf3576112ac`.
Both frozen Step-0 comparisons report 0 differences; all four authoring projections
match. Snapshot G has one tolerated unseeded shape variance in
`tests_ce/integration_tests/test_entity/patient.xml`: `de_patients.allergies`
is `array<unknown>` there and `array<str>` in the final run. Snapshot H also
records `array<str>`.

The capture covers 454 successful descriptors, 62 expected errors, 16 files that
are not descriptors, and 76 unchanged unrunnable outcomes. Another 322 are
unverified by this oracle: 273 service descriptors, 40 standalone authoring
fixtures, and 9 dependent fixtures. The later test/oracle/evidence commits change
no production or XML descriptor files.

Three of the 9 XLSX-dependent descriptors were compared separately against the
frozen Step-0 checkout with the same 12-row workbook fixture. The full captured
rows match byte-for-byte: `read_random_seeded.xml` (12), `read_paged_ordered.xml`
(12), and `read_cumulated_seeded.xml` (200). Both canonical capture files have
SHA-256 `6d206b67c795442d93ef398a2ef25636ee036e3193d4eecf2b4a1b5473abb7ac`.
The runner asserted the imported CE checkout in both processes. The automated
inventory still skips all 9; this separate proof leaves 319 entries without a
Step-0-versus-HEAD comparison. The fixture-dependency classifier now has positive
and negative self-tests for exact writes, unrelated writes, rebinding, function
scope, and conditional paths. Its static evidence remains conservative, not a
proof that arbitrary Python fixture setup executes.

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

Ruff and full-package MyPy pass. `make lint` fails at Pylint with exit 30. With
Pylint 3.3.7, frozen code and experiment have the same 24 error-severity
findings by symbol and message. Total findings are 3,509 versus 3,707 in the
latest paired run, mainly 212 additional convention messages. Historical
lint debt is not hidden by changing the gate.

## Verdicts after Amendment 12

- **Structure reached, locally:** exact layout and component rules pass with complete
  coverage, an empty violation list, zero material unknown positions, and no budget rise.
  This is checked with the publicly installed ArchKeel 0.6.1 package, not a local
  candidate. It does not prove behavior or test quality.
- **Behavior preserved for the comparable oracle set:** both frozen comparisons have zero
  differences. Three more XLSX cases match exactly in isolated comparison. The
  remaining 319 without comparison prevent an unqualified all-descriptors claim.
- **Delivery not ready:** `make lint` remains red, the complete external-service
  suite has not passed in one isolated run, and remote CE CI has not run. No CE merge or
  release is justified by the structural verdict alone.
