# Step 08C32: close fail-open DSL oracle cases

Independent Luna test, implementation, and review passes found that the Step-0
comparator accepted a missing object field or union alternative. It also
recorded a dynamic `<generate count="{...}">` as `dynamic` instead of measuring
the produced rows. The negative tests were red before the fixes; all eight
targeted tests pass afterward. The child now rejects an import outside its
explicit checkout root.
Only numeric Python test-source line references are normalized; path and
assertion text remain compared. No production code or XML changed.

A serial full pair at frozen `a219163e` and target `f312a455`, using the same
guarded child and one worker, inventoried all 930 XMLs. Both authoring
projection sets match. Frozen: 454 captured, 62 expected errors, 16
non-descriptors, 76 unrunnable, 322 unverified. Target: 453, 62, 16, 77,
322. The stricter comparator reports **two differences**, not acceptance:

- `tests_ce/functional_tests/test_casting_type/test_data_type.xml`: target
  logged successful generation of 50 rows but exited 0 without the oracle
  result marker. Three isolated guarded reruns per checkout captured 50 rows
  every time. The lost result did not recur; its cause is unknown.
- `tests_ce/integration_tests/test_memstore_api/test_memstore_sum_and_count.xml`:
  dynamic unseeded `te` count was 21 frozen versus 17 target. Earlier isolated
  repeats also varied on unchanged frozen code (15, 17, 17) and target code
  (21, 13, 13). This cannot prove fixed-count parity or a regression.

Snapshot SHA-256: frozen
`49d2c98fd5a3d404312e0b4e284b13b76cccbfec46144d6854c756e9e845a2b7`,
target
`c451c4d97453674cffdff6f15b34d851a922beb6cfc3310148bc136d072ecc9f`.
The old 0-difference result used a weaker comparator and is not the current
behavioral verdict. Do not rerun until a lucky green value appears.

Local gates: 1,173 unit tests passed, 11 skipped; Ruff passed; full-package
MyPy passed for 474 files; ArchKeel 0.6.1 baseline and `--against eafc119f`
passed with 0 violations and unknown positions. `make lint` still fails at
the pre-existing Pylint Error 30; Ruff passes. Remote CE CI has not run.
