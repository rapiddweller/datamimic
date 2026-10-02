# Step 08C13: eliminate DSL and IO type escapes

## Change

- Replaced every DSL and IO `Any`, cast, reflective lookup, and type-ignore finding with explicit
  types or runtime shape checks.
- Kept scalar JSON compatibility in `FileUtil` while record consumers reject non-record roots.
- Exposed the recursive JSON value type through the existing domain-facing `dataset_api`; no new
  component edge or private crossing was added.
- Added the missing local `isodate` type surface instead of suppressing its imports.

## Evidence

- ArchKeel violations: 321 -> 272; 47 baseline fingerprints resolved and 0 added.
- DSL NO-MAGIC findings: 21 -> 0. IO NO-MAGIC findings: 28 -> 0.
- `private_crossings` remains 0; unresolved calls remain at 1,403; typed positions improve
  454 -> 421.
- Independent final gate: 485 targeted tests passed. The implementation gate also passed 1,141
  unit tests (11 skipped), 544 integration tests (2 skipped), and 132 functional tests.
- Existing OrbStack MongoDB pagination gate: 5 passed; no service was started. PostgreSQL runtime
  behavior remains unverified because the available suites mutate shared schemas.
- Full descriptor oracle before the final compatibility corrections: 930 compared, 0 differences,
  and 3 permitted unseeded optional-shape variances. The corrected serializer and JSON paths then
  passed focused compatibility probes; all four Authoring projection hashes remain unchanged.
- Ruff and diff check pass. Full-package mypy reports only the two existing missing optional Ray
  imports.

The first full oracle run missed one child result for `test_script_dict.xml`; two isolated reruns
and a second full run captured it. This is recorded as an observed harness flake, not an exclusion.
