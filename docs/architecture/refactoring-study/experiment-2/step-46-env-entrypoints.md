# Step 46: explicit dotenv startup

[Amendment 68](amendment-68.md) replaces the old root-import bootstrap target.
The root package no longer loads `.env`; CLI and MCP executable entrypoints
load startup-cwd `.env` without overriding process variables, before importing
the application graph. Runtime settings resolve on use. Descriptor
`.env.properties` selection is untouched. Independent review found that merely
moving `load_dotenv()` into `main()` was too late: eager CLI/MCP package imports
had already frozen Domain dataset paths. Lazy package exports and a command
module fix the order; subprocess tests cover both `.env` and process precedence.

The current local ArchKeel candidate scans 491/491 Python files with 100% AST
coverage. It still reports 97 violations, 76 new baseline positions and 189
material UNKNOWN positions. This slice changes a behavior ArchKeel does not
currently measure; the unchanged violation count is not a failed refactor.

The local oracle inventoried all 930 XML files: 383 captured, 70 expected
errors, 16 non-descriptors, 77 unrunnable and 384 unverified. All 109 captured
seeded cases match the previous CE capture in result and output digests. The
existing comparator flags 17 unseeded captures; 16 vary again in a same-edition
repeat. The remaining XML-export case keeps the same 30 rows and shard-size
multiset (6, 12, 12), but assigns those sizes to file names differently. This
is evidence of shard-order variance, not proof of universal parity.

LOCAL VERIFIED: 1,472 unit tests passed (11 skipped, one xfailed), 14 dotenv
entrypoint tests, five target-definition tests, five exporter tests, Ruff,
full-package MyPy, Pylint cyclic-import gate, isolated-wheel CLI/MCP help and
CLI `.env` startup, local ArchKeel report, full local descriptor oracle, and
`git diff --check`. CI and service-backed descriptors were not run. The branch
contains other uncommitted experiment changes; this slice is not yet committed
or ready for a PR.
