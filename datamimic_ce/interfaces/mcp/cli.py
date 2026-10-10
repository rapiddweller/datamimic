"""Command line interface for serving the FastMCP endpoint.

Typer does not support ``typing.Literal`` for these option types, so explicit
enums define the transport choices at the boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from dotenv import load_dotenv

from datamimic_ce._compat import StrEnum

app = typer.Typer(help="Run the DATAMIMIC MCP adapter")

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8765


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
        str | None,
        typer.Option(help="Host interface to bind for SSE transport"),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option(help="TCP port to bind for SSE transport"),
    ] = None,
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

    from datamimic_ce.interfaces.mcp import server as mcp_server

    if transport == Transport.stdio:
        mcp_server.create_server().run(Transport.stdio.value)
        return

    resolved_host = host if host is not None else os.getenv("DATAMIMIC_MCP_HOST", _DEFAULT_HOST)
    try:
        resolved_port = port if port is not None else int(os.getenv("DATAMIMIC_MCP_PORT", str(_DEFAULT_PORT)))
    except ValueError as exc:
        raise typer.BadParameter("DATAMIMIC_MCP_PORT must be an integer") from exc

    sse_app = mcp_server.build_sse_app(mcp_server.create_server(), os.getenv("DATAMIMIC_MCP_API_KEY"))
    uvicorn.run(
        sse_app,
        host=resolved_host,
        port=resolved_port,
        log_level=log_level.value,
    )


def main() -> None:
    load_dotenv(Path.cwd() / ".env", override=False)
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
