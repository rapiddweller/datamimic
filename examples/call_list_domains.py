"""Quick helper to list available MCP domains."""

import anyio
from fastmcp.client import Client

from datamimic_ce.mcp.server import create_server


async def _main() -> None:
    async with Client(create_server()) as client:
        tools = await client.list_tools()
        print("Tools:", ", ".join(sorted(tool.name for tool in tools)))
        domains = await client.call_tool("list_domains")
        print(domains[0].text)


if __name__ == "__main__":
    anyio.run(_main)
