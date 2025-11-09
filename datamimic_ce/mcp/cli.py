"""Command line interface for serving the FastMCP endpoint.

WHY: Typer in some environments doesn't support ``typing.Literal`` for
option types, raising "Type not yet supported". To keep broad
compatibility without upgrading tooling, we use ``Enum`` for choices.
This keeps the CLI thin, explicit, and compatible across Typer versions.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Annotated

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

# WHY: Avoid ruff-bugbear B008 (no function calls in argument defaults).
# We compute environment-derived defaults at module load and use them as
# plain defaults, while passing Typer options via `Annotated` metadata.
_ENV_HOST_DEFAULT = os.getenv("DATAMIMIC_MCP_HOST", _DEFAULT_HOST)
_ENV_PORT_DEFAULT = int(os.getenv("DATAMIMIC_MCP_PORT", str(_DEFAULT_PORT)))


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
