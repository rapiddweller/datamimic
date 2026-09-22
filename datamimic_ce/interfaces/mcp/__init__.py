"""Public entrypoints for the MCP integration."""

from .server import create_server, mount_mcp

__all__ = ["create_server", "mount_mcp"]
