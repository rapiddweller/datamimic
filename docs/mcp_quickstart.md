# Optional MCP adapter

The CLI is the baseline interface. Install CE 5.0 from PyPI in your Python 3.11+
project environment, adding MCP only when your client uses it:

```bash
python -m pip install "datamimic-ce[mcp]"
datamimic-mcp --transport stdio --workspace-root "/absolute/path/to/project"
```

Both transports use the same typed Authoring application. `version`, `schema`,
`capabilities` and `capability` accept their named arguments directly. `reference`,
codec, lint and bounded-run requests use `{"request": {...}}`; `datamimic_build` takes `{}` and proves the workspace root as a project. Follow each
tool's advertised input schema.

| MCP tool | CLI equivalent |
|---|---|
| `datamimic_version` | `datamimic authoring version` |
| `datamimic_schema` | `datamimic authoring schema --name <name>` |
| `datamimic_capabilities` | `datamimic authoring capabilities [--full]` |
| `datamimic_capability` | `datamimic authoring capability --domain <domain> --name <name>` |
| `datamimic_reference` | `datamimic authoring reference --topic <topic> [--name <name>]` |
| `datamimic_compile` | `datamimic authoring compile -` |
| `datamimic_decompile` | `datamimic authoring decompile -` |
| `datamimic_build` | `datamimic authoring build <workspace-root>` |
| `datamimic_lint` | `datamimic authoring lint -` |
| `datamimic_dry_run` | `datamimic authoring dry-run -` |
| `datamimic_run` | `datamimic authoring run -` |

Persist XML. `datamimic_build` proves the workspace root as a project: its
`datamimic.xml` against `acceptance/build.json`, which holds expectations,
`product_roles`, origin-tagged `acceptance_requirements` and smoke/replay options.
Compile/decompile readiness proves syntax; a ready Build also carries bounded
acceptance evidence. Target isolation does not prove delivery to an external sink.

`--workspace-root` binds the host-owned project directory independently of the
server's launch directory. It must be an existing directory. Omit it to retain
the launch-directory default. Inline XML/DM JSON and logical descriptor paths use
that root. The option does not change the process working directory or its host
environment. The Python `create_server` factory also accepts `workspace_root`
and descriptor identity. No schema resources or
MCP-only compiler are registered.

## Codex

Install the adapter in the project's environment. Add a stdio entry to Codex's
MCP configuration using its absolute executable and project paths:

```toml
[mcp_servers.datamimic_ce]
command = "/absolute/path/to/project/.venv/bin/datamimic-mcp"
args = ["--transport", "stdio", "--workspace-root", "/absolute/path/to/project"]
```

Run `codex mcp get datamimic_ce` and start a new session in that project.

## Claude Code

From the project directory:

```bash
claude mcp add --transport stdio --scope local datamimic_ce -- \
  /absolute/path/to/project/.venv/bin/datamimic-mcp \
  --transport stdio --workspace-root "/absolute/path/to/project"
claude mcp get datamimic_ce
```

In either client, list tools, call `datamimic_reference` with
`{"request": {"topic": "assembly", "name": "starter"}}`, and verify a read of a
known project-relative fixture before authoring. The [agent plugin](agent_plugin.md)
adds the shared workflow; it does not silently install or configure this adapter.
For a remote Platform project use its [HTTP/OAuth guide](https://docs.datamimic.io/advanced/connect-mcp-client/).

## SSE

```bash
datamimic-mcp --transport sse --host 127.0.0.1 --port 8765 --workspace-root "/absolute/path/to/project"
```

`DATAMIMIC_MCP_API_KEY` enables `Authorization: Bearer <key>` or `X-API-Key: <key>`
for SSE. Stdio uses its owning process's access controls.
