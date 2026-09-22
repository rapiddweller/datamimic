# Step 0 — contract freeze

## Inputs

- source: `development` at `a219163e533d661bcc7bda0faa5ecc77909ab5aa`
- ArchKeel: `0.6.0` at `d14035b31ef2addac9cfea738a70d8643df2f7ae`
- target contract: `architecture-contract.json`
- accepted debt: `known-violations.json`

## Architecture observation

| Measure | Step 0 |
|---|---:|
| Files discovered/read/parsed | 458 / 458 / 458 |
| AST coverage | 100% |
| Rule violations reported | 1,471 |
| Baseline violation fingerprints | 1,331 |
| Cycle edges | 243 |
| Private crossings | 2 |
| Typing positions | 496 |
| Untyped private accesses | 4 |
| Calls unresolved | 1,363 of 11,321 |
| Call resolution | 73.8% |

`declared_rules=FAIL` is the expected target distance. Observation completeness is `PASS`; there are
no open decisions or diagnostics.

Largest rule groups:

- `INTERFACES-ONLY`: 576
- `NO-MAGIC-CONTROL-FLOW`: 508
- `REQUIRES-COMPLETE`: 120
- physical placement: DSL 107, runtime 68, IO 35, domains 16, resources 9, interfaces 7
- `ROOT-LAYOUT`: 24
- `NO-COMPONENT-CYCLES`: 1 component-cycle finding

## Behavior evidence

- `tests_ce/architecture` plus all `tests_ce/unit_tests/test_authoring`:
  `1,928 passed, 14 skipped`.
- capabilities full JSON: 187,014 bytes,
  SHA-256 `b068f56ea06710d1f26a8b3a27fb1faafdfe52fd6a7ee2c180587c6279831496`.
- authoring reference JSON: 8,757 bytes,
  SHA-256 `7c99444c15b8a869c4b1b213c758488042ef8cd84ca559dd4e91b2da4a2778f1`.
- overview reference JSON: 465 bytes,
  SHA-256 `4f15cf9b7f18c1d991a8bb258510bfa40ab720a15e44b73bba6eb8201f83048b`.

The first pytest attempt could not open the existing plugin's localhost coordination socket inside
the sandbox. The unchanged command passed after that local socket was allowed; this is environment
evidence, not a test retry.

## ArchKeel 0.6.0 findings before implementation

1. `boundary_types` for a target API with no function returns `UNKNOWN` and cannot be baselined.
   The rule will be added with the first real API function.
2. A layout violation whose package `__init__.py` is empty produces an empty evidence excerpt and
   then fails ArchKeel's own complete-trace check. Ownership-only docstrings make those existing
   violations baselineable without changing behavior.
