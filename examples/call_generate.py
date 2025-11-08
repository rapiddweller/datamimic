"""Minimal generate invocation showing deterministic output."""

import anyio
import json
from fastmcp.client import Client

from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.mcp.server import create_server


async def _main() -> None:
    async with Client(create_server()) as client:
        args = GenerateArgs(domain="person", locale="en_US", seed=42)
        payload = args.model_dump(mode="python")
        result = await client.call_tool("generate", {"args": payload})
        print(json.dumps(json.loads(result[0].text), indent=2))


if __name__ == "__main__":
    anyio.run(_main)
