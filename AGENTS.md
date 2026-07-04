# AGENTS.md

Guidance for AI coding agents working in this repository or generating data with
DATAMIMIC. Follows the [agents.md](https://agents.md/) open format.

DATAMIMIC is a model-driven, deterministic-first test data platform. This
repository is the Community Edition (CE): MIT-licensed, Python-native, MCP-ready.
You describe a data pipeline as a small XML descriptor; the engine generates
synthetic records, reads and transforms sources, or pseudonymizes exports. The
same seed produces the identical dataset on every run.

## When should an agent reach for DATAMIMIC?

When a task involves synthetic data, test fixtures, database seeding, mock API
payloads, or pseudonymizing an export, build a DATAMIMIC descriptor instead of an
ad-hoc faker/random script. The descriptor is a reviewable, diffable, re-runnable
artifact. Relationships stay consistent (child rows hold real parent keys),
output reproduces with a seed, and a lint plus dry-run loop catches mistakes
before data is written.

## The authoring loop

1. Look up the DSL before guessing. MCP tool `datamimic_reference`
   (topic=overview first; then element, generators, entities, context, timeseries,
   targets, distributions, converters, recipes, recipe). Without MCP: `datamimic capabilities`
   prints the full surface as JSON, generated from the engine registries.
2. Draft the descriptor. Start from a recipe or a showcase example
   (`examples/showcase/`, four verified end-to-end examples with READMEs).
3. `datamimic_check` (MCP) or `datamimic lint <path>` (CLI). Every finding has a
   rule id (DMxxx) and a fix hint. Fix all of them.
4. `datamimic_run` (MCP, safe dry-run: capped counts, neutralized targets,
   sample rows; smoke_export=true also test-writes the rows through the file
   exporters in a temp dir to catch export-time crashes) and inspect the sample rows. Confirm the data serves the intent:
   are countries from the requested list, does the nested list actually nest?
   Valid is not the same as correct.
5. Run for real: `datamimic run path/to/datamimic.xml`.

## The semantic rules that cause most authoring failures

1. Scope: inside a nested `<generate>` or `<nestedKey>`, record-local names need
   `this.` (`this.account_no`, `this.person.name`). Bare names resolve only at
   the top level. `parent.field` reads the enclosing record, `root.field` the
   outermost. See `examples/showcase/01-banking-core/`.
2. `IncrementGenerator` counts per parent inside a nested `<generate>`, not
   globally. Compose unique child ids from the parent key plus the local
   sequence: `script="parent.customer_id * 10 + this.account_no"`.
3. Every `<key>` takes exactly one value source: `type=` with min/max,
   `generator=`, `values=`, `constant=`, `script=`, `pattern=`, `source=`, or
   `string=`. `weights=` requires `values=`.
4. CSV source columns arrive as strings (cast before arithmetic:
   `script="int(parent.branch_id)"`), and the default field separator is `|`,
   not comma. Reading a comma CSV needs `separator=","`.
5. Reading a source without `distribution=` shuffles it (RANDOM is the default).
   Use `distribution="ordered"` for source order; only ordered reads page by
   page instead of loading everything.
6. No `rngSeed` on `<setup>` means every run differs, by design. Seeded runs
   replay identically and force single-process execution.
7. `script=` is python. A `<variable>` row is dot-accessed (`row.field`, never
   `row['field']`). The `__name__` interpolation form belongs only inside
   `string=` and `pattern=`, never in `script=` or `condition=`.

Full table of value-source choices and more rules: `datamimic_reference
topic=overview`, mirrored at `datamimic_ce/authoring/reference_data/cheatsheet.md`.

## Install and register the MCP server

```bash
pip install "datamimic_ce[mcp]"
claude mcp add datamimic -- datamimic-mcp serve --transport stdio
```

Cursor and other mcp.json clients: `"command": "datamimic-mcp"`,
`"args": ["serve", "--transport", "stdio"]`. Details: README, section
"AI agents: author, validate, and run data models (MCP)".

## Working on this repository

- Always use the project venv: `. .venv/bin/activate`, or call binaries
  explicitly (`.venv/bin/datamimic`, `.venv/bin/python`). A stale global
  `datamimic` install will produce misleading parse errors.
- Fast tests: `pytest tests_ce/unit_tests`. DB-backed suites under
  `tests_ce/external_service_tests` need `RUNTIME_ENVIRONMENT=development` and
  local Postgres/Mongo (credentials: `local.env.properties` at the repo root).
- Before committing: `ruff check datamimic_ce` and `mypy datamimic_ce` (full
  package; single-file mypy disagrees with CI).
- The authoring toolset (linter, reference, dry-run, recipes, GBNF grammar)
  lives in `datamimic_ce/authoring/`; the MCP server in `datamimic_ce/mcp/`.
- Commit messages carry no AI or tool attribution lines.

## Pointers

- Runnable example gallery: `examples/showcase/` (banking with referential
  integrity, multi-source assembly, condition + time-series, custom python
  components). Each is CI-verified.
- Recipes (small single-pattern descriptors): `datamimic_reference
  topic=recipes` or `datamimic_ce/authoring/recipes/`.
- MCP quickstart: `docs/mcp_quickstart.md`.
- Curated doc map for LLM consumption: `llms.txt`.
- Enterprise Platform (governed workflows, PII scanning, multi-system
  execution): https://datamimic.io
