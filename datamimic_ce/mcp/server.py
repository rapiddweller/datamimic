"""Optional MCP transport for the canonical authoring service."""

from __future__ import annotations

from typing import Protocol

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from datamimic_ce.authoring import service
from datamimic_ce.authoring.contracts import (
    CheckRequest,
    ReferenceRequest,
    ReferenceResult,
    RunRequest,
    RunResult,
    ScaffoldRequest,
    ScaffoldResult,
)
from datamimic_ce.authoring.diagnostics import LintResult


class MountableApplication(Protocol):
    def mount(self, path: str, app: Starlette) -> None: ...


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Starlette, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        authorization = request.headers.get("authorization")
        bearer = authorization.removeprefix("Bearer ") if authorization else None
        token = bearer or request.headers.get("x-api-key")
        if token != self.api_key:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": "invalid_api_key"})
        return await call_next(request)


def create_server() -> FastMCP:
    server = FastMCP(name="datamimic-ce", version=None)

    @server.tool("datamimic_check")
    async def datamimic_check(request: CheckRequest) -> LintResult:
        return service.check(request)

    @server.tool("datamimic_run")
    async def datamimic_run(request: RunRequest) -> RunResult:
        return service.run(request)

    @server.tool("datamimic_reference")
    async def datamimic_reference(request: ReferenceRequest) -> ReferenceResult:
        return service.reference(request)

    @server.tool("datamimic_scaffold")
    async def datamimic_scaffold(request: ScaffoldRequest) -> ScaffoldResult:
        return service.scaffold(request)

    return server


def build_sse_app(server: FastMCP, api_key: str | None = None) -> Starlette:
    application = server.sse_app()
    if api_key:
        application.add_middleware(APIKeyMiddleware, api_key=api_key)
    return application


def mount_mcp(
    application: MountableApplication,
    *,
    path: str = "/mcp",
    api_key: str | None = None,
    server: FastMCP | None = None,
) -> FastMCP:
    mcp_server = server or create_server()
    application.mount(path, build_sse_app(mcp_server, api_key))
    return mcp_server


__all__ = ["build_sse_app", "create_server", "mount_mcp"]
