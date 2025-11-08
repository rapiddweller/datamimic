"""Command line interface for serving the FastMCP endpoint.

WHY: Typer in some environments doesn't support ``typing.Literal`` for
option types, raising "Type not yet supported". To keep broad
compatibility without upgrading tooling, we use ``Enum`` for choices.
This keeps the CLI thin, explicit, and compatible across Typer versions.
"""

from __future__ import annotations

import os
from enum import Enum

import typer
import uvicorn

from datamimic_ce.mcp.server import (
    HTTP_MIDDLEWARE_ATTR,
    build_sse_app,
    create_server,
)

app = typer.Typer(help="Run the DataMimic MCP server")

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765


class Transport(str, Enum):
    """Supported transport mechanisms for FastMCP.

    WHY: Replaces ``Literal['sse', 'stdio']`` to avoid Typer limitations.
    """

    sse = "sse"
    stdio = "stdio"


class LogLevel(str, Enum):
    """Supported log levels for uvicorn.

    WHY: Replaces ``Literal[...]`` to avoid Typer limitations.
    """

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


@app.command()
def serve(
    host: str = typer.Option(
        os.getenv("DATAMIMIC_MCP_HOST", _DEFAULT_HOST),
        help="Host interface to bind for SSE transport",
    ),
    port: int = typer.Option(
        int(os.getenv("DATAMIMIC_MCP_PORT", str(_DEFAULT_PORT))),
        help="TCP port to bind for SSE transport",
    ),
    transport: Transport = typer.Option(
        Transport.sse,
        help="FastMCP transport (sse for network clients, stdio for agent runtimes)",
    ),
    log_level: LogLevel = typer.Option(
        LogLevel.info,
        help="Log level when running the SSE server",
    ),
) -> None:
    """Start the FastMCP server with optional API key gating."""

    api_key = os.getenv("DATAMIMIC_MCP_API_KEY")
    server = create_server(api_key=api_key)
    middleware = getattr(server, HTTP_MIDDLEWARE_ATTR, None)

    if transport == Transport.stdio:
        # WHY: stdio transport is typically embedded; it does not honour host/port.
        server.run(Transport.stdio.value)
        return

    sse_app = build_sse_app(server, middleware)
    uvicorn.run(
        sse_app,
        host=host,
        port=port,
        log_level=log_level.value,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
