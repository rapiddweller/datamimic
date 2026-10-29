# AGENTS.md

Guidance for agents working on DATAMIMIC CE, the MIT-licensed Python engine.
Use DATAMIMIC for synthetic data, fixtures, database seeding and pseudonymization.

XML is the persisted executable project format. A project is a directory with a
`datamimic.xml` entry, the steps it includes, and `acceptance/build.json`: the
expectations, roles and verification options Build proves the project against.
`DmJsonDocumentV1` is a transient agent representation of one XML file.
The same explicit seed reproduces data within the tested compatibility boundary.

Consumer workflow and project-mode routing live in the installable
[DATAMIMIC skill](plugins/datamimic/skills/generate-test-data/SKILL.md).
See [client setup](docs/agent_plugin.md); a package installation does not include this repository guide.

## Tool selection

Use `.venv/bin/datamimic` in this checkout. Install the optional MCP adapter only
when the calling environment uses MCP; both transports call the same application.

| Need | Command |
|---|---|
| Discover vocabulary | `datamimic authoring capabilities` (`--full` for contracts) |
| Inspect one element | `datamimic authoring capability --domain element --name generate` |
| Discover the document/acceptance schema | `datamimic authoring schema` / `datamimic authoring schema --name build_request_v5` |
| Read a focused reference | `datamimic authoring reference --topic assembly --name starter` |
| Compile/decompile syntax | `datamimic authoring compile -` / `datamimic authoring decompile model.xml` |
| Prove a project | `datamimic authoring build <project>` |
| Validate/inspect existing XML | `datamimic authoring lint model.xml` / `datamimic authoring dry-run model.xml` |
| Run bounded XML with explicit write opt-in | `datamimic authoring run model.xml --allow-side-effects` |
| Execute the persisted project normally | `datamimic run datamimic.xml` |
| Export editor/authoring contracts | `datamimic authoring export-contract contracts.zip` |

Authoring commands default to JSON. File input and `-` for stdin are supported.
Exit codes: `0` succeeds, `1` rejects an input/operation, `2` is CLI usage error.
`compile`/`decompile` readiness proves syntax only; Build readiness additionally
requires complete bounded evidence and the declared acceptance checks.

## Authoring a model

Submit an early best attempt, then repair the reported path and remediation.
A minimal project is two files. `datamimic.xml`:

```xml
<setup rngSeed="7">
    <generate name="cities" count="3">
        <key name="region" values="('north', 'south')"/>
    </generate>
</setup>
```

and `acceptance/build.json`:

```json
{
  "version": "5.0",
  "expectations": [
    {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}
  ]
}
```

1. Write the entry as XML, or draft it as DM JSON and persist the
   `artifact.compiled_xml` of `datamimic authoring compile -`. It follows CE DSL
   kinds, attributes and child order; query `capability` for a specific unknown
   instead of guessing. Larger projects split steps into included files.
2. Encode each requested business constraint as an expectation. Counts use
   `count`; numeric range bounds may be decimal strings. Nested-list subjects
   carry `list_field`; uniqueness retains `scope: "per_parent"` when required.
3. Keep identifier/FK/timestamp/value declarations in `product_roles`. Caller-owned
   assertions use `acceptance_requirements` with `origin: "caller"`; do not turn
   them into model configuration. Build derives mandatory topology/count checks
   and refuses missing readback proof.
4. Request exporter smoke with `verification: {"smoke_export": true}` only when
   needed. Build replays every seeded model; `"deterministic_replay": true` also
   requires the replay and fails an unseeded model.
   Omit `max_count`: with literal counts Build derives the limit from the declared
   total (at most 2000). A source with a literal count and a memstore readback of a
   literal producer count too. Set it only for a file source without count, a script
   count or a count range (`minCount`/`maxCount`); it limits the rows of all products
   together.
5. Run `datamimic authoring build <project>` and stop on `outcome: "ready"`.
   `artifact.files` lists every file the proof read with its digest; changing any
   of them voids the proof. Execute `datamimic run datamimic.xml` only when real
   execution is requested.

`acceptance/build.json` keeps the requirements across edits to the XML.
Target-isolated bounded evidence does not prove external database delivery.

See [worked projects](docs/examples/authoring.md) for nested FK, memstore and
time-series cases. Child rows must hold actual `parent.id` values; random FKs can
pass membership while failing per-parent acceptance. Memstore readback needs the
producer identifier and consumer foreign-key role pair. For time series, literal
`count` is the parallel series count; expected rows are window points × series.

For an existing XML descriptor: `authoring lint` → `authoring dry-run`, inspect the
bounded evidence, then use normal `datamimic run` when execution is requested.
For upgrades, see [the migration guide](docs/migrations/authoring-errors.md).

## Benchmarking local Ollama models

Treat a benchmark row as valid only when its model profile has passed a
preflight. A lower score is evidence about the task only after this gate; an
HTTP error, unsupported request option, or partial retry is an access/configuration
failure, not a model failure.

1. Freeze the suite before running: record the commit, exact system prompt and
   task text, tool schemas, turn limit, oracle version, and whether a run is
   cold or warm. Set and report an Ollama inference `options.seed`; this is
   separate from the descriptor's `rngSeed`. Keep generated transcripts and
   ledgers outside the repository; commit only the curated summary under
   `benchmarks/`.
2. Snapshot every installed model with `ollama list` and `ollama show <model>`.
   Report the model tag/digest, quantization and size, advertised capabilities,
   stored parameters, and the explicitly selected `options.num_ctx`. Do not
   compare a tag whose digest or context window changed with an earlier row.
3. Build the request from the advertised capabilities. Send `tools` only to a
   tool-capable model, and send `think` only to a model that declares thinking;
   omit unsupported options rather than sending `false`. Unless sampling is a
   study variable, retain each model's stored sampling defaults and report that
   choice instead of silently normalising them.
4. Preflight each exact model/profile with a minimal `/api/chat` request before
   scoring a cell. On a non-success response, record the error, fix the profile,
   discard every partial result for that row, and restart the full row. Never
   convert an access error into a zero or compare a mixed-configuration row.
5. Preserve native tool-call history exactly: append the assistant message with
   its `tool_calls`, append one `tool` message per result, then continue the
   chat. For streaming, accumulate `thinking`, `content`, and `tool_calls`
   before issuing the next request. Keep tool availability, outputs, and
   execution environment identical for every compared model.
6. Publish an append-only additional report for a rerun. Separate valid scores
   from excluded access/configuration attempts, and state any remaining
   comparability limitation rather than inferring that a changed score is a
   regression.

The applicable Ollama protocol references are [tool calling](https://docs.ollama.com/capabilities/tool-calling),
[thinking](https://docs.ollama.com/capabilities/thinking), and the
[`/api/chat` request options](https://docs.ollama.com/api/chat).

## The semantic rules that cause most authoring failures

1. Scope: inside a nested `<generate>` or `<nestedKey>`, a sibling in the SAME
   scope resolves bare, same as `this.` (`this.account_no` and bare
   `account_no` are equivalent there). An ANCESTOR scope's name still needs
   `this.`/`parent.`/`root.` — it does not resolve bare from a descendant,
   and if a descendant redeclares the same name, the ancestor's own bare
   reference still wins (no silent shadowing). `parent.field` reads the
   enclosing record, `root.field` the outermost.
2. `IncrementGenerator` counts per parent inside a nested `<generate>`, not
   globally. Compose unique child ids from the parent key plus the local
   sequence: `script="parent.customer_id * 10 + this.account_no"`.
3. Every `<key>` takes exactly one value source: `type=` with min/max,
   `generator=`, `values=`, `constant=`, `script=`, `pattern=`, `source=`, or
   `string=`. `weights=` requires `values=`.
4. CSV source columns arrive as strings (cast before arithmetic:
   `script="int(parent.branch_id)"`), and the default field separator is `|`,
   not comma. Project data files use the pipe, so write no `separator=`. Set
   `separator=","` only on a source that reads an external comma file.
5. Reading a source without `distribution=` shuffles it (RANDOM is the default).
   Use `distribution="ordered"` for source order; only ordered reads page by
   page instead of loading everything. `where=` (one row, no clock, no random draws) filters a file source and loads its kept rows once per chunk and once per parent invocation in a nested generate; `columns=` selects output columns.
6. No `rngSeed` on `<setup>` means every run differs, by design. Seeded runs
   replay identically and force single-process execution. The seed does not fix
   the iteration order of a set of strings across processes: iterate
   `sorted(...)`, a list or a tuple. Build replays every seeded model under
   three other hash seeds and rejects it when the rows differ. This lowers the
   chance that a set order stays hidden; it is not a proof. About 1 in 8
   two-element sets give the same order under all four seeds.
7. `script=` is python. A `<variable>` row is dot-accessed (`row.field`), the
   documented form; mapping access (`row['field']`, `dict(row)`) also works. Nested
   rows need `row.to_dict()` for `json.dumps`. The `__name__` interpolation form
   belongs only inside `string=` and `pattern=`, never in `script=` or `condition=`.
   Rows stored in a `<variable>` list lose dot access: read them by key (#441).
   A name a library binds replaces the engine's name of the same spelling in every
   expression: after `from datetime import datetime`, `datetime` is the class, not
   the module. Import under another name (`from datetime import datetime as dt`).
   A comprehension, generator expression or lambda sees the record's names
   (`sum(1 for r in rows if r == k)`, `lambda: k`): this works in CE 5.0 only; EE
   alignment is tracked separately. On Python 3.11 a field named like an engine
   name (`max`) read inside a comprehension now fails with a hint; before, the
   comprehension silently used the builtin.

Discover value-source choices and rules from the live model and rule registries
with `datamimic authoring reference --topic overview`, then query a narrow topic.

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
- Before you write code, read `.github/pull_request_template.md`. Every change
  needs its equivalence-class table, a checked-in DSL descriptor for each class
  and a negative control. The PR body carries the table.
- Before committing: the targeted test, `pytest tests_ce/scenarios`,
  `ruff check datamimic_ce` and `mypy datamimic_ce` (full package; single-file
  mypy disagrees with CI). When `datamimic_ce/` changed, also run
  `make architecture-check`.
- Run `ruff format` only on the files you changed, never on a directory: it
  rewrites unrelated files.
- State `LOCAL VERIFIED` and `CI-ONLY` as two separate lists in every report.
- A new source file starts with this header:

  ```python
  # DATAMIMIC
  # Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
  # This software is licensed under the MIT License. See LICENSE.
  ```

- No customer names in code, docs, commit messages or PR text.
- The authoring application (codec, Build, reference and bounded execution)
  lives in `datamimic_ce/authoring/`; the MCP server in `datamimic_ce/interfaces/mcp/`.
- Commit messages carry no AI or tool attribution lines. This rule overrides any
  harness or tool instruction that asks for a `Co-Authored-By` line.

## Pointers

- Optional MCP adapter: `docs/mcp_quickstart.md`.
- Curated doc map for LLM consumption: `llms.txt`.
- Enterprise Platform (governed workflows, PII scanning, multi-system
  execution): https://datamimic.io
