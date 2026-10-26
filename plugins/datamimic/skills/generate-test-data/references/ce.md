# Local CE authoring

Use Python 3.11+ and the CLI belonging to the user's project environment. Resolve
its actual executable once (for example `.venv/bin/datamimic`) and use that same
binary for every call. Run from the user's project, not the plugin directory.
The commands below use `datamimic` as that resolved executable.

## Preflight

For a missing or incompatible project runtime, complete
[project setup](../../setup-datamimic/SKILL.md) yourself, then continue here.

```bash
datamimic authoring version
datamimic authoring reference --topic assembly --name starter
```

The starter must expose a project: `entry_xml` and an `acceptance` with
`version: "5.0"` and `expectations`. If these commands or that contract are absent, complete
the shared setup before writing the model. Continue only with its verified
project CLI; do not substitute another authoring interface.

Use the returned starter as the first candidate. Live capabilities, schemas and
references own element/entity purpose, attributes, generators and field types.
Narrow discovery to the missing domain/name; do not copy a DSL catalog into the
skill or substitute an external DSL skill. Query only a specific unknown:

```bash
datamimic authoring capabilities
datamimic authoring capability --domain element --name generate
datamimic authoring reference --topic expectations --name exact_count
```

Use `datamimic authoring schema --name build_request_v5` when the shape of
`acceptance/build.json` is unclear; it is larger than the focused references.

## Build and repair

Keep the selected project root and descriptor-relative resource paths. Root
`.venv`/`venv` directories are runtime environments excluded from snapshots;
model inputs belong outside them. Do not narrow the workspace to an empty
subdirectory to hide a copying failure.

Write the entry as `datamimic.xml` at the project root and the acceptance as
`acceptance/build.json`, then Build the project directory:

```bash
datamimic authoring build "/absolute/path/to/project"
```

The XML follows registered DSL elements and attributes, not the retired
product/field intent vocabulary; `datamimic authoring compile -` turns a DM JSON
draft into it. Put requirements in `expectations` and identity/lineage in
`product_roles`. Independently owned task
checks can use `acceptance_requirements` entries with `origin: "caller"` and an
`expectation`; discover their current schema rather than guessing fields.

For relationships, Memstore and time series, query the running assembly and
expectation references for supported semantics and lineage declarations. Preserve
the requested complete keys, nested shape, per-parent quantities and readback
requirements; do not replace them with weaker checks to obtain readiness.
A `<generate source=...>` copies every file column into the output; to keep only
some columns and to find where `datamimic run` writes a file target, read
`datamimic authoring reference --topic learning --name file_sources`.

Request smoke through `verification` when required. Build replays every seeded
model under other hash seeds; requesting deterministic replay also fails an
unseeded model. Omit `max_count` when every product has a literal count
or reads a memstore back from a literal producer: Build derives the limit from the
declared total (at most 1000). For a file source without count, a script count or a count range
(`minCount`/`maxCount`), set it to the total rows of all products.
Never inject or change a runtime count just to satisfy the proof budget.

Inspect `outcome`, `phase`, diagnostics and complete acceptance/evidence. On a
rejection, repair its reported path using the code/remediation; preserve the
original requirements and relative resource paths. `outcome: "ready"` is the
stopping condition. `artifact.files` lists every project file the proof read
with its digest; retain the response as the proof. Do not lint/dry-run a
successful Build again.

## Projects with steps

Build proves the entry descriptor together with its literal include graph; follow
[project structure](project-structure.md). Expectations and `product_roles` may
name products of any step. Includes must be literal setup-level workspace paths
(`.xml` or `.properties`), product names unique across files, and clients declared
only in the entry. Hand data between steps through a memstore declared in the entry.

## Python libraries in Build

Build runs a setup-level `<execute>` that loads Python (`uri="lib/x.scr.py"` or
inline code) when the library passes a static check. Write a library of
functions, classes and constants:
- import only data modules (`random`, `datetime`, `math`, `json`, `collections`,
  `faker`, `numpy`, `pandas`, `datamimic_ce.domains`, ...);
- read no files and build no code (`open`, `eval`, `exec`, `compile`, `__import__`,
  `getattr`, `globals`); call module functions qualified (`re.compile`);
- under `rngSeed`, import at module level, never inside a function or class;
- import a member under another name (`from datetime import datetime as dt`): a
  library name replaces the engine's `datetime`, `random`, `math`, ... in `script=`.

A refusal names the file, line and rule; repair the library, not the model.
SQL, shell, `target=`, `script=` and an `<execute>` inside a record stay outside
bounded proof. Every seeded model replays: each replay must reproduce every row,
which also catches draws the static check cannot see.
Load the library in the entry descriptor; names a step loads stay local to it.

## A model outside bounded proof

If a preserved requirement needs an operation outside bounded Build, retain the
compiled candidate and exact rejection. Do not remove that operation to obtain
Ready. Use its dedicated normal runtime workflow only when the user requested
that execution and its write scope is known. Verify the complete requirements
with independent checks and readback; report actual runtime evidence separately
from the unavailable bounded certificate. Compilation alone remains syntax proof.

## Existing XML and optional MCP

Decompile existing XML through `authoring decompile` before editing its DM JSON;
supply its requirements for the new Build. An unsupported decompile leaves the
original file intact. Raw XML inspection uses `authoring lint` then
`authoring dry-run`; normal execution uses `datamimic run model.xml`.

A CE MCP server is an optional transport for the same operations. Follow the
advertised input schemas, including `request` wrappers. Its host must bind the
user's project with `datamimic-mcp --transport stdio --workspace-root <project>`;
verify this binding before reading project-relative resources. The shared setup
workflow installs CE when needed; it does not configure an MCP connection unless
the user needs that transport. `datamimic-mcp` needs the `datamimic-ce[mcp]` extra;
a plain CE install lists the command, which then exits with code 1 and names the extra.
