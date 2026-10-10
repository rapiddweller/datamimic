"""Public entrypoints for the MCP integration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .server import create_server, mount_mcp

__all__ = ["create_server", "mount_mcp"]


def __getattr__(name: str) -> object:
    if name == "create_server":
        from .server import create_server

        return create_server
    if name == "mount_mcp":
        from .server import mount_mcp

        return mount_mcp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
