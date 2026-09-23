# Experiment 2 verification, 2026-09-23

## State

- CE branch: `experiment/target-architecture-v2` at `9d5e9c5c`.
- The final local ArchKeel checker is `789784e1` (package `0.6.1.dev57`). The frozen
  0.6.0 tag remains the Step-0 control; it cannot parse Amendment 11's
  `allowed_positions` field.
- The contract scan is complete (474/474 files), with 0 violations, 0 unknown
  positions, and `declared_rules=PASS`. The violation baseline is empty.
- Measurement budgets are still positive and unchanged: 1,288 unresolved calls,
  171 cycle edges, 144 typing positions, and 3 untyped private accesses.

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
fixtures, and 9 dependent fixtures. The later test-only commit `9d5e9c5c` changes
no production, XML, or adjacent XML test-evidence files.

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
with fully matched local fixture settings. The current run does not prove those
six against today's service configuration.

Ruff and full-package MyPy pass. `make lint` fails at Pylint with exit 30. The
frozen code also exits 30 with 24 error-severity findings; total Pylint findings
rose from 3,508 to 3,701, mainly convention messages.

## Open acceptance decisions

Protocol item 2 says to validate without a baseline. ArchKeel requires
`--baseline` when `measurement_budgets` are declared, so that exact gate exits 2.
The baseline-backed gate passes with an empty violation list, but positive
budgets. Protocol item 8's `make lint` and complete current external-service
suite are also not green. Do not call the experiment fully accepted or release
ready until these facts are dispositioned explicitly.
