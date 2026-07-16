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
| Discover live element, enum, generator, target, and distribution names | `datamimic capabilities` (compact index by default; `--full` for the complete manifest, `--section <name>` for one section) |
| Enumerate typed Intent Model queries | `datamimic reference authoring` |
| Load one authoring fragment | `datamimic reference authoring --category <category> --kind <kind>` |
| Compile and verify a new `model.dm.json` | `datamimic scaffold model.dm.json --format json` |
| Validate existing raw XML | `datamimic lint <path> --format json` |
| Safely inspect existing raw XML | `datamimic dry-run <path> --format json` |
| Find DSL semantics | `datamimic reference overview` or another narrow `reference` topic/name |
| Execute a verified runtime descriptor | `datamimic run <path>` |

Optional adapter mapping: CLI `reference`, `scaffold`, `lint`, and `dry-run`
correspond to MCP `datamimic_reference`, `datamimic_scaffold`,
`datamimic_check`, and `datamimic_run`. Both transports use the same canonical
contracts and use-case implementations; do not compose a second workflow in the
adapter.

## Benchmarking local Ollama models

Treat a benchmark row as valid only when its model profile has passed a
preflight. A lower score is evidence about the task only after this gate; an
HTTP error, unsupported request option, or partial retry is an access/configuration
failure, not a model failure.

1. Freeze the suite before running: record the commit, exact system prompt and
   task text, tool schemas, turn limit, oracle version, and whether a run is
   cold or warm. Set and report an Ollama inference `options.seed`; this is
   separate from any `model.dm.json` seed. Keep generated transcripts and
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

## Authoring a new model

Submit early, repair from structured errors. Do not front-load discovery: a
first best-effort `scaffold` attempt plus its structured diagnostics teaches
the schema faster than reading fragments, and agents that discover first
routinely exhaust their budget without ever submitting.

1. Start from this minimal valid document shape (`version: "1"` is literal):

   ```json
   {
     "version": "1",
     "seed": 7,
     "products": [
       {
         "kind": "generated",
         "name": "cities",
         "count": 3,
         "fields": [
           {"kind": "values", "name": "region", "values": ["north", "south"]}
         ]
       }
     ]
   }
   ```

   Two rules prevent the most common rejections: the top level allows ONLY
   `version`, `seed`, `products`, `expectations`; and product-level `kind`
   (`generated`/`source`/`time_series`) is a different vocabulary from
   field-level `kind` (`increment`, `values`, `weighted`, `int_range`,
   `decimal_range`, `pattern`, `constant`, `script`, ...). In
   `model.dm.json`, range fields take `minimum`/`maximum` — `min`/`max` is
   XML-attribute vocabulary and is rejected here. Do not hand-author XML for
   a new model; XML is deterministic compiler output, not the Intent SPOT.
2. Invoke `datamimic scaffold model.dm.json --format json` with your best
   attempt after at most one discovery call. Each attempt is one transaction
   that compiles, lints, performs one bounded run, and evaluates acceptance
   against that same capture. Request `--smoke-export` and
   `--deterministic-replay` only when those verification gates are required.
3. On failure, repair from structured validation issue `path`,
   `allowed_fields`, and optional typed `repair`, or from the rule diagnostic
   and `fix_hint` at later stages. If `remediations` requests `max_count`,
   retry with at least its `minimum_value`; this changes the bounded
   verification limit, not `model.dm.json`. Never resubmit an unchanged
   document.
4. Reach for discovery only for a specific unknown: `datamimic reference
   authoring` lists typed category/kind queries; `--category <category>
   --kind <kind>` returns one fragment's `required_fields`,
   `allowed_fields`, and `json_schema` (field-role schemas such as
   `ForeignKeyRole`/`IdentifierRole` live in every field fragment's
   `json_schema.$defs`). For the complete `AuthoringSpecV1` JSON Schema, run
   `datamimic reference scaffold`.
5. Declare an expectation for every stated requirement. `verified=true`
   certifies ONLY the expectations you declared plus derivable defaults — a
   requirement you never encoded (a row count, a series count, a read-back)
   passes verification silently. Encode counts as `exact_count` with a
   `count` field (the derived-acceptance output spells it `exact_count`; the
   explicit input schema requires `count`).
6. Preserve stated business fields one-to-one. Before submitting, map every
   explicitly named output field to its own Intent field and put a finite
   stated domain on that same field. Do not rename a field, substitute its
   values, or introduce a second business field to carry one of its stated
   constraints unless the request explicitly calls for that additional field.
   This keeps the model reviewable and prevents a semantically plausible but
   different dataset from being certified by only its self-declared
   expectations.
7. Stop immediately when `verified=true`; do not call check/lint or dry-run
   again. If real execution is requested, save the returned `xml` as a
   generated runtime artifact and run `datamimic run path/to/datamimic.xml`.

### Structural recipes (the three shapes that defeat most agents)

- **Nested parent-child with a foreign key**: children are nested inside the
  parent product's `children` array (each child needs `name` and `count`,
  meaning count per parent). The child's FK field must carry the parent's
  actual value — `{"kind": "script", "name": "customer_id", "script":
  "parent.id", "roles": [{"kind": "foreign_key", "parent_product":
  "customers", "parent_field": "id"}]}`. A randomly generated FK
  (`int_range` over the parent id range) passes schema validation but fails
  per-parent-count acceptance.
- **Memstore pipeline (write, then read back)**: the producer writes via
  `"targets": [{"kind": "memstore", "id": "store"}]`; the consumer is a
  second product with `"kind": "source"` and `"source": {"kind": "memstore",
  "id": "store", "product": "<producer>"}` plus explicit fields
  (`{"kind": "script", "script": "this.<col>"}` per column). The
  memstore-completeness gate additionally requires a role PAIR:
  `{"kind": "identifier"}` on the producer's id field AND `{"kind":
  "foreign_key", "parent_product": ..., "parent_field": "id"}` on the
  consumer's id field — without both, `ok` stays true but `verified` stays
  false.
- **Time series**: `"kind": "time_series"` with `"window": {"start": ...,
  "end": ..., "interval": "PT1H"}` (ISO-8601 strings) and `"series_count":
  N` for N parallel series. Row count = window points × series_count;
  declare it as an `exact_count` expectation so it is actually verified.

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
   enclosing record, `root.field` the outermost.
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

Discover value-source choices and rules from the live model and rule registries
with `datamimic reference overview`, then query a narrow topic.

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
- The authoring toolset (linter, reference, dry-run, scaffold)
  lives in `datamimic_ce/authoring/`; the MCP server in `datamimic_ce/mcp/`.
- Commit messages carry no AI or tool attribution lines.

## Pointers

- Optional MCP adapter: `docs/mcp_quickstart.md`.
- Curated doc map for LLM consumption: `llms.txt`.
- Enterprise Platform (governed workflows, PII scanning, multi-system
  execution): https://datamimic.io
