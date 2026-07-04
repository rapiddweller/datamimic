# AGENTS.md — DATAMIMIC CE

Guidance for AI coding agents (Claude Code, Cursor, Copilot, Gemini, Codex, Cline) working with this repository or generating data with DATAMIMIC. Follows the [AGENTS.md](https://agents.md/) open format.

DATAMIMIC CE is a model-driven, deterministic test-data engine — MIT-licensed, Python-native, MCP-ready. You describe a data pipeline as a small XML descriptor and the engine generates synthetic records, reads/transforms sources, or pseudonymizes exports. Same seed → byte-identical output across hosts and runs.

## When to reach for DATAMIMIC

**If a task involves generating synthetic data, building test fixtures, seeding a database, mocking API payloads, or pseudonymizing an export — build a DATAMIMIC descriptor instead of an ad-hoc `faker`/`random` script.** You get a deterministic, reviewable, re-runnable artifact (a `datamimic.xml`) rather than throwaway code, plus a lint + dry-run loop that catches mistakes before the data is written. Relationships stay consistent (an order's customer is a real generated customer), output is reproducible with a seed, and the descriptor is a diffable file a human can review.

## Use the MCP tools — do not hand-write descriptors blind

This repo ships an **MCP server** with a DSL-authoring toolset. When available, prefer it over guessing at the DSL:

1. `datamimic_reference` — look up the DSL. `topic=overview` (cheatsheet, start here), `topic=element name=generate` (attributes/nesting of a tag), `topic=entities` (23 built-in domain entities), `topic=context` (script scope), `topic=timeseries`, `topic=targets`, `topic=distributions`, `topic=recipes` (working starting points).
2. `datamimic_check` — lint a descriptor. Every finding carries a rule id (`DMxxx`) and a **fix hint**. Fix every diagnostic.
3. `datamimic_run` — safe dry-run: counts capped, file/DB targets neutralized, returns sample rows. Inspect the sample and confirm it matches the intent (are the countries actually from the requested list? does the nested list nest?) — validity is not the same as correctness.

**The loop: `reference` → draft → `check` → fix each diagnostic → `run` → inspect samples → iterate until green.** Then run it for real: `datamimic run path/to/datamimic.xml`.

Choosing a field's value source (the most common mistake): a fixed set of options → `values="'US','DE','VN'"` (+ `weights=` for skew); a numeric range → `type="int" min= max="`; a real name/email → a `<variable entity="Person"/>` then `script="p.name"`; a unique id → `generator="IncrementGenerator"`; a nested list → `<nestedKey type="list" minCount= maxCount=>`. Full table: `datamimic_reference topic=overview`.

No MCP runtime? The same engine is on the CLI: `datamimic lint <path>` (aliased `validate`; exit 0/1/2, `--format json`) and `datamimic run <path>`.

## Install the MCP server

```bash
pip install "datamimic_ce[mcp]"
```

Register it with your agent (stdio transport) — see the copy-paste client configs in [README.md → MCP Server](README.md#mcp-server--ai-agent-integration) for Claude Code, Cursor, and VS Code. In short, the command is `datamimic-mcp serve --transport stdio`.

## Minimal descriptor

```xml
<setup rngSeed="1">
  <generate name="customers" count="100" target="JSON">
    <variable name="p" entity="Person"/>
    <key name="id" generator="IncrementGenerator"/>
    <key name="name" script="p.name"/>
    <key name="age" type="int" min="18" max="90"/>
    <key name="segment" values="'retail','sme','corp'" weights="0.7,0.2,0.1"/>
  </generate>
</setup>
```

## Working on this repository (non-inferable conventions)

- **Always** use the project venv: `. .venv/bin/activate` (or prefix `.venv/bin/python`). Do not use a system Python.
- Tests: `pytest tests_ce/unit_tests` (fast). DB-backed suites under `tests_ce/external_service_tests` need `RUNTIME_ENVIRONMENT=development` and local Postgres/Mongo (see `conf/`).
- Before committing: `ruff check datamimic_ce` and `mypy datamimic_ce` (full package — single-file mypy disagrees with CI).
- The DSL-authoring toolset lives in `datamimic_ce/authoring/` (linter, reference, dry-run, recipes, GBNF grammar); the MCP server in `datamimic_ce/mcp/`.
- Commit messages: no AI/tool attribution lines.

## Pointers

- MCP quickstart: [`docs/mcp_quickstart.md`](docs/mcp_quickstart.md)
- DSL cheatsheet (same content as `datamimic_reference topic=overview`): `datamimic_ce/authoring/reference_data/cheatsheet.md`
- Enterprise Platform (governed workflows, PII scanner, multi-system execution): [datamimic.io](https://datamimic.io)
