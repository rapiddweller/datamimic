# DATAMIMIC MCP Quickstart

This guide walks through installing and exercising the Model Context Protocol (MCP) surface that wraps the existing DataMimic domain facade.

## Installation

```bash
pip install datamimic-ce[mcp]
```

The optional `mcp` extra pulls in `fastmcp`, `uvicorn`, and the additional runtime pieces needed for the server and tests.

For local development against a checkout, install the package in editable mode so the test suite can import the optional transport client:

```bash
pip install -e .[mcp]
```

## Running the server

Launch the MCP server via the dedicated CLI:

```bash
export DATAMIMIC_MCP_HOST=127.0.0.1
export DATAMIMIC_MCP_PORT=8765
# Optional API key gate – clients must send the same token via `Authorization: Bearer` or `X-API-Key`
export DATAMIMIC_MCP_API_KEY=changeme

datamimic-mcp
```

Environment variables override the Typer command options so deployments can be tuned without altering scripts:

- `DATAMIMIC_MCP_HOST` (default `127.0.0.1`, only used for SSE transport)
- `DATAMIMIC_MCP_PORT` (default `8765`, only used for SSE transport)
- `DATAMIMIC_MCP_API_KEY` (unset disables authentication)

## IDE configuration

### Claude Desktop (YAML)

```yaml
mcpServers:
  datamimic:
    command: datamimic-mcp
    args: ["--host", "127.0.0.1", "--port", "8765"]
    env:
      DATAMIMIC_MCP_API_KEY: changeme
```

### Cursor (JSON)

```json
{
  "mcpServers": {
    "datamimic": {
      "command": "datamimic-mcp",
      "args": ["--host", "127.0.0.1", "--port", "8765"],
      "env": {
        "DATAMIMIC_MCP_HOST": "127.0.0.1",
        "DATAMIMIC_MCP_PORT": "8765"
      }
    }
  }
}
```

Both snippets assume the CLI is on `PATH`. Remove the API key entry if the server is running without authentication.

## Example interactions

### List domains

```python
import anyio
from fastmcp.client import Client
from datamimic_ce.mcp.server import create_server

async def main():
    async with Client(create_server()) as client:
        response = await client.call_tool("list_domains")
        print(response[0].text)

anyio.run(main)
```

Sample output (truncated):

```json
[{"domain":"person","version":"v1","request_fields":["domain","version","count","seed","locale","profile_id","component_id","constraints","clock"],"defaults":{"domain":"person","version":"v1","count":1,"seed":"0","locale":"en_US"}}, ...]
```

### Generate deterministic people

```python
import anyio, json
from fastmcp.client import Client
from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.mcp.server import create_server

async def main():
    args = GenerateArgs(domain="person", locale="en_US", seed=42, count=2)
    async with Client(create_server()) as client:
        payload = args.model_dump(mode="python")
        first = await client.call_tool("generate", {"args": payload})
        second = await client.call_tool("generate", {"args": payload})
        print(json.loads(first[0].text) == json.loads(second[0].text))  # True

anyio.run(main)
```

The `determinism_proof.content_hash` field and the canonical JSON comparisons will match across identical requests, ensuring byte-identical payloads for the same seed lineage.

### Payments domain example

```python
args = GenerateArgs(domain="address", locale="de_DE", seed=7, count=1)
```

Running the snippet twice with the same seed yields identical addresses. Switching `seed` alters the content hash and record values without touching structural metadata.

## Security and guardrails

- **Authentication** – set `DATAMIMIC_MCP_API_KEY` to require clients to present the same token via `Authorization: Bearer <token>` or the `X-API-Key` header. Requests lacking the correct key receive `401` responses.
- **Resource caps** – the `GenerateArgs.count` field is capped at `10_000`. Larger requests fail validation before reaching domain code.
- **Profile selectors** – `profile_id` and `component_id` are mutually exclusive. The model validator raises immediately if both are supplied.
- **Deterministic clock** – the `clock` attribute defaults to `2025-01-01T00:00:00Z` to preserve reproducibility while still allowing overrides.

## Additional resources

- `examples/call_list_domains.py` – prints the registered tools and domain catalogue.
- `examples/call_generate.py` – emits sample person records using `seed=42`.
- `make typecheck`, `make lint`, and `make coverage` – convenience targets for the strict quality gates (mypy `--strict`, pylint ≥ 9.0, coverage ≥ 90%).

Happy generating!
