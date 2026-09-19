# Optional MCP adapter

The DATAMIMIC CLI is the baseline interface. Install MCP only when the calling
environment already uses MCP:

```bash
pip install "datamimic-ce[mcp]"
datamimic-mcp --transport stdio
```

The adapter exposes exactly four tools. Each accepts the same typed request and
returns the same typed result as the corresponding authoring service operation:

| MCP tool | CLI equivalent |
|---|---|
| `datamimic_reference` | `datamimic reference` |
| `datamimic_scaffold` | `datamimic scaffold` |
| `datamimic_check` | `datamimic lint` |
| `datamimic_run` | `datamimic dry-run` |

There are no MCP-only generators, domain catalogs, schema resources, recipes,
or alternate authoring workflows. Query `datamimic_reference` with
`topic=authoring` for the live Intent Model surface, then submit one canonical
`AuthoringSpecV1` document to `datamimic_scaffold`.

For SSE transport:

```bash
datamimic-mcp --transport sse --host 127.0.0.1 --port 8765
```

Set `DATAMIMIC_MCP_API_KEY` to require either `Authorization: Bearer <key>` or
`X-API-Key: <key>` on SSE requests. API-key policy does not apply to stdio.
