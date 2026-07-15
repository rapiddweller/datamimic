"""Command line interface for serving the FastMCP endpoint.

Typer does not support ``typing.Literal`` for these option types, so explicit
enums define the transport choices at the boundary.
"""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Annotated

import typer
import uvicorn

from datamimic_ce.mcp.server import (
    build_sse_app,
    create_server,
)

app = typer.Typer(help="Run the DATAMIMIC MCP adapter")

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765

# WHY: Avoid ruff-bugbear B008 (no function calls in argument defaults).
# We compute environment-derived defaults at module load and use them as
# plain defaults, while passing Typer options via `Annotated` metadata.
_ENV_HOST_DEFAULT = os.getenv("DATAMIMIC_MCP_HOST", _DEFAULT_HOST)
_ENV_PORT_DEFAULT = int(os.getenv("DATAMIMIC_MCP_PORT", str(_DEFAULT_PORT)))


class Transport(StrEnum):
    """Supported transport mechanisms for FastMCP.

    WHY: Replaces ``Literal['sse', 'stdio']`` to avoid Typer limitations.
    """

    sse = "sse"
    stdio = "stdio"


class LogLevel(StrEnum):
    """Supported log levels for uvicorn.

    WHY: Replaces ``Literal[...]`` to avoid Typer limitations.
    """

    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"


@app.callback(invoke_without_command=True)
def serve(
    host: Annotated[
        str,
        typer.Option(help="Host interface to bind for SSE transport"),
    ] = _ENV_HOST_DEFAULT,
    port: Annotated[
        int,
        typer.Option(help="TCP port to bind for SSE transport"),
    ] = _ENV_PORT_DEFAULT,
    transport: Annotated[
        Transport,
        typer.Option(
            help="FastMCP transport (sse for network clients, stdio for agent runtimes)",
        ),
    ] = Transport.sse,
    log_level: Annotated[
        LogLevel,
        typer.Option(help="Log level when running the SSE server"),
    ] = LogLevel.info,
) -> None:
    """Start the MCP adapter using stdio or SSE transport."""

    api_key = os.getenv("DATAMIMIC_MCP_API_KEY")
    server = create_server()

    if transport == Transport.stdio:
        server.run(Transport.stdio.value)
        return

    sse_app = build_sse_app(server, api_key)
    uvicorn.run(
        sse_app,
        host=host,
        port=port,
        log_level=log_level.value,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
