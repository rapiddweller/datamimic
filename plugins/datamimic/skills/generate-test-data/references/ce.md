# Local CE authoring

Use Python 3.11+ and the CLI belonging to the user's project environment. Resolve
its actual executable once (for example `.venv/bin/datamimic`) and use that same
binary for every call. Run from the user's project, not the plugin directory.
The commands below use `datamimic` as that resolved executable.

## Preflight

```bash
datamimic authoring version
datamimic authoring reference --topic assembly --name starter
```

The starter must expose a transaction with `version: "4.0"`, a `document.root`
and `expectations`. If these commands or that contract are absent, stop before
writing the model. Explain that the runtime needs CE 5.0 or a compatible source
preview. PyPI 4.3.0 has the retired Scaffold interface. Use the project's approved
installation source; keep its environment and dependency manager.

Use the returned starter as the first candidate. Query only a specific unknown:

```bash
datamimic authoring capabilities
datamimic authoring capability --domain element --name generate
datamimic authoring reference --topic expectations --name exact_count
```

Use `datamimic authoring schema --name build_request_v4` when the transaction
shape itself is unclear; it is larger than the focused references.

## Build and repair

Submit the transaction through stdin with an explicit absolute project root:

```bash
datamimic authoring build - --workspace-root "/absolute/path/to/project"
```

DM JSON follows registered DSL nodes (`kind`, `properties`, ordered `children`),
not the retired product/field intent vocabulary. Put requirements in
`expectations` and identity/lineage in `product_roles`. Independently owned task
checks can use `acceptance_requirements` entries with `origin: "caller"` and an
`expectation`; discover their current schema rather than guessing fields.

- Nested FK: copy the actual `parent.id`; declare producer identifier and child
  foreign-key roles, and check `per_parent_count`. Random valid parent IDs do
  not prove the right number of children per parent.
- Memstore: declare the store, producer and ordered consumer. The producer's
  identifier plus the consumer's foreign-key role pair establishes readback;
  assert the consumer count and required copied values.
- Time series: `generate.count` is the parallel-series count. The end of the
  window is exclusive. Assert points per window multiplied by series count.

Request smoke/replay through `verification` when required; deterministic replay
needs an explicit seed. Increase `max_count` only to capture the intended proof.
Never inject or change a runtime count just to satisfy the proof budget.

Inspect `outcome`, `phase`, diagnostics and complete acceptance/evidence. On a
rejection, repair its reported path using the code/remediation; preserve the
original requirements and relative resource paths. `outcome: "ready"` is the
stopping condition. Persist `artifact.compiled_xml` in the chosen project and
retain the separate proof. Do not lint/dry-run a successful Build again.

## Existing XML and optional MCP

Decompile existing XML through `authoring decompile` before editing its DM JSON;
supply its requirements for the new Build. An unsupported decompile leaves the
original file intact. Raw XML inspection uses `authoring lint` then
`authoring dry-run`; normal execution uses `datamimic run model.xml`.

A CE MCP server is an optional transport for the same operations. Follow the
advertised input schemas, including `request` wrappers. Its host must bind the
user's project with `datamimic-mcp --transport stdio --workspace-root <project>`;
verify this binding before reading project-relative resources. A plugin install
alone does not install CE or configure that server.
