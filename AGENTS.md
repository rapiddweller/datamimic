# AGENTS.md

Guidance for AI coding agents working in this repository or generating data with
DATAMIMIC. Follows the [agents.md](https://agents.md/) open format.

DATAMIMIC is a model-driven, deterministic-first test data platform. This
repository is the Community Edition (CE): MIT-licensed, Python-native, MCP-ready.
For new models, describe the business intent in `model.dm.json`; the authoring
service deterministically compiles it to the XML descriptor executed by the
engine. Existing XML descriptors remain supported. The same seed produces the
identical dataset on every run.

## When should an agent reach for DATAMIMIC?

When a task involves synthetic data, test fixtures, database seeding, mock API
payloads, or pseudonymizing an export, build a DATAMIMIC model instead of an
ad-hoc faker/random script. `model.dm.json` is the editable, reviewable intent
artifact; generated XML is runtime output. Relationships stay consistent (child
rows hold real parent keys), output reproduces with a seed, and bounded
verification catches mistakes before data is written.

## Tool selection

The project CLI is the baseline contract. In this checkout, invoke it as
`.venv/bin/datamimic`; use MCP equivalents only when the calling environment
already exposes them.

| Need | CLI command |
|---|---|
| Discover live element, enum, generator, target, and distribution names | `datamimic capabilities` |
| Enumerate typed Intent Model queries | `datamimic reference authoring` |
| Load one authoring fragment | `datamimic reference authoring --category <category> --kind <kind>` |
| Compile and verify a new `model.dm.json` | `datamimic scaffold model.dm.json --format json` |
| Validate existing raw XML | `datamimic lint <path> --format json` |
| Safely inspect existing raw XML | `datamimic dry-run <path> --format json` |
| Find recipes or DSL semantics | `datamimic reference recipes` or another narrow `reference` topic/name |
| Execute a verified runtime descriptor | `datamimic run <path>` |

Optional adapter mapping: CLI `reference`, `scaffold`, `lint`, and `dry-run`
correspond to MCP `datamimic_reference`, `datamimic_scaffold`,
`datamimic_check`, and `datamimic_run`. Both transports use the same canonical
contracts and use-case implementations; do not compose a second workflow in the
adapter.

## Authoring a new model

1. Query the Intent Model before guessing. Run `datamimic reference authoring`
   to list typed category/kind queries, then request only the fragment needed,
   for example `datamimic reference authoring --category field --kind weighted`
   or `datamimic reference authoring --category source --kind memstore`.
2. Create one canonical `model.dm.json` with `version: "1"`. Do not hand-author
   XML for a new model; XML is deterministic compiler output, not the Intent SPOT.
3. Invoke `datamimic scaffold model.dm.json --format json`. Each attempt is one
   transaction that compiles, lints, performs one bounded run, and evaluates
   acceptance against that same capture. Request `--smoke-export` and
   `--deterministic-replay` only when those verification gates are required.
4. On failure, repair from structured validation issue `path`, `allowed_fields`,
   `expected_fragment`, and optional typed `repair`, or from the rule diagnostic
   and `fix_hint` at later stages. If `remediations` requests
   `max_count`, retry with at least its `minimum_value`; this changes the bounded
   verification limit, not `model.dm.json`. Use a narrower authoring reference
   query if needed. Never repeat an identical failed call without changing its
   input or requested verification parameter.
5. Stop immediately when `verified=true`; do not call check/lint or dry-run again.
   If real execution is requested, save the returned `xml` as a generated runtime
   artifact and run `datamimic run path/to/datamimic.xml`.

## Working with an existing raw XML descriptor

1. Look up the DSL before guessing with `datamimic reference overview` and then
   the narrow DSL topic/name.
2. Run `datamimic lint <path> --format json` and fix every diagnostic.
3. Run `datamimic dry-run <path> --format json` once; inspect the bounded
   samples because valid is not the same as correct. `--smoke-export`
   additionally exercises file exporters in a temporary dir.
4. Run the verified descriptor for real with `datamimic run <path>`.

## The semantic rules that cause most authoring failures

1. Scope: inside a nested `<generate>` or `<nestedKey>`, a sibling in the SAME
   scope resolves bare, same as `this.` (`this.account_no` and bare
   `account_no` are equivalent there). An ANCESTOR scope's name still needs
   `this.`/`parent.`/`root.` — it does not resolve bare from a descendant,
   and if a descendant redeclares the same name, the ancestor's own bare
   reference still wins (no silent shadowing). `parent.field` reads the
   enclosing record, `root.field` the outermost. See
   `examples/showcase/01-banking-core/`.
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

Full table of value-source choices and more rules: `datamimic reference overview`,
mirrored at `datamimic_ce/authoring/reference_data/cheatsheet.md`.

## Install the CLI

```bash
pip install datamimic-ce
```

The MCP adapter is optional. Install it with `pip install "datamimic-ce[mcp]"`
only when the calling environment uses MCP; see `docs/mcp_quickstart.md` for
registration details.

## Working on this repository

- Always use the project venv: `. .venv/bin/activate`, or call binaries
  explicitly (`.venv/bin/datamimic`, `.venv/bin/python`). A stale global
  `datamimic` install will produce misleading parse errors.
- Fast tests: `pytest tests_ce/unit_tests`. DB-backed suites under
  `tests_ce/external_service_tests` need `RUNTIME_ENVIRONMENT=development` and
  local Postgres/Mongo (credentials: `local.env.properties` at the repo root).
- Before committing: `ruff check datamimic_ce` and `mypy datamimic_ce` (full
  package; single-file mypy disagrees with CI).
- The authoring toolset (linter, reference, dry-run, recipes, scaffold)
  lives in `datamimic_ce/authoring/`; the MCP server in `datamimic_ce/mcp/`.
- Commit messages carry no AI or tool attribution lines.

## Pointers

- Runnable example gallery: `examples/showcase/` (banking with referential
  integrity, multi-source assembly, condition + time-series, custom python
  components). Each is CI-verified.
- Recipes (small single-pattern descriptors): `datamimic reference recipes`
  or `datamimic_ce/authoring/recipes/`.
- Optional MCP adapter: `docs/mcp_quickstart.md`.
- Curated doc map for LLM consumption: `llms.txt`.
- Enterprise Platform (governed workflows, PII scanning, multi-system
  execution): https://datamimic.io
