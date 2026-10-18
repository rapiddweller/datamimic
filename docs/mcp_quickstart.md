# Optional MCP adapter

The CLI is the baseline interface. Install MCP only for environments that use it:

```bash
pip install "datamimic-ce[mcp]"
datamimic-mcp --transport stdio
```

Both transports use the same typed Authoring application. Tool requests are wrapped
as `{"request": {...}}` for the request-based operations below; discovery tools
accept their named arguments directly.

| MCP tool | CLI equivalent |
|---|---|
| `datamimic_version` | `datamimic authoring version` |
| `datamimic_schema` | `datamimic authoring schema --name <name>` |
| `datamimic_capabilities` | `datamimic authoring capabilities [--full]` |
| `datamimic_capability` | `datamimic authoring capability --domain <domain> --name <name>` |
| `datamimic_reference` | `datamimic authoring reference --topic <topic> [--name <name>]` |
| `datamimic_compile` | `datamimic authoring compile -` |
| `datamimic_decompile` | `datamimic authoring decompile -` |
| `datamimic_build` | `datamimic authoring build -` |
| `datamimic_lint` | `datamimic authoring lint -` |
| `datamimic_dry_run` | `datamimic authoring dry-run -` |
| `datamimic_run` | `datamimic authoring run -` |

Persist XML. DM JSON is transient; expectations, `product_roles`, origin-tagged
`acceptance_requirements`, and smoke/replay options belong to `BuildRequestV4`.
Compile/decompile readiness proves syntax; a ready Build also carries bounded
acceptance evidence. Target isolation does not prove delivery to an external sink.

The server's working directory is its host-owned workspace. Inline XML/DM JSON and
logical descriptor paths use that root. The Python `create_server` factory can bind
an explicit `workspace_root` and descriptor identity. No schema resources or
MCP-only compiler are registered. Legacy scaffold/check tools are retired; see
[the migration guide](migrations/authoring-errors.md).

For SSE:

```bash
datamimic-mcp --transport sse --host 127.0.0.1 --port 8765
```

`DATAMIMIC_MCP_API_KEY` enables `Authorization: Bearer <key>` or `X-API-Key: <key>`
for SSE. Stdio uses its owning process's access controls.
