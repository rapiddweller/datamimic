# Step 10: CLI layout and coverage gate

Starting revision: `9f34791f40bbf9db0d21af4dfda4368e63d18eab`. Amendment 17 narrows the
physical target: the four CLI files now form `interfaces/cli/`, with the existing
`datamimic_ce.interfaces.cli:app` entry and `python -m` behavior preserved. The independent
Luna implementation and test passes were reviewed separately; integration caught one stale
test import. A third Luna pass added the unit-coverage gate, and an independent read-only
Luna review found no further actionable issue.

The curated report-only `benchmarks/dsl-authoring/` archive moved byte-for-byte under
`docs/benchmarks/`. `factory/` remains because it is a documented and tested Python API;
removing it needs a compatibility decision, not a file move. Root `stubs/` remains the
`mypy_path` for third-party `.pyi` files, outside the CE package root.

## Local verification

- CLI targeted tests: 61 passed, including real module invocation and usage exit code 2.
- Unit gate: 1,173 passed, 11 skipped. Serial Coverage.py 7.16.1 reports 65.9806% lines
  (15,099/22,884) across all 460 non-demo CE Python files. The unimported factory
  implementation is included at 0%; the interim CI floor is 65.74%, not the 90% goal.
- Other non-external suites, serial: 2,612 passed, 17 skipped, one localhost-SSE test
  deselected because the sandbox denies socket binding.
- Ruff and full-package MyPy pass; ArchKeel 0.6.1 reads 476/476 files and reports 0
  violations, 0 material unknown positions, and no baseline delta. Its unresolved-call
  budget narrowed from 1,279 to 1,278. The new nested layout rule passes.
- All 930 XML paths are still in the oracle inventory, and no XML file changed. The four
  authoring/CLI projection hashes match before and after the move under the same venv.

The frozen capability hash alone is not portable to this borrowed venv: its installed
package metadata reports `schema_version=4.2.1.dev4+dirty`, so the old absolute hash fails
even before the CLI move. The first broad run also failed because I forced
`RUNTIME_ENVIRONMENT=development`: local properties redirected several SQLite targets.
The failing DBUnit case passes without that override; the complete non-external rerun above
used the normal environment. Neither failure is counted as a product regression.

No full 930-result old/new replay, disposable external-service matrix, remote CI, or
current all-suite coverage measurement is claimed by this step. Those remain separate
merge evidence, not reasons to weaken the architecture contract.
