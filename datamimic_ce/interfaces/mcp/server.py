"""Optional MCP transport for the canonical authoring service."""

from __future__ import annotations

import secrets
from pathlib import Path, PurePosixPath
from typing import Protocol

from anyio import to_thread
from fastmcp import FastMCP
from pydantic import JsonValue
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from datamimic_ce.authoring import AuthoringApplication, create_authoring_application
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain, CapabilityLookupResult
from datamimic_ce.authoring.domain.reference import ReferenceResult
from datamimic_ce.authoring.domain.requests import (
    DEFAULT_AUTHORING_DESCRIPTOR_PATH,
    PROJECT_ENTRY_PATH,
    AuthoringSchemaId,
    BuildResult,
    CompileDocumentRequest,
    CompileDocumentResult,
    DecompileDocumentRequest,
    DecompileDocumentResult,
    LintRequest,
    LintResult,
    ReferenceRequest,
    RunRequest,
    RunResult,
)
from datamimic_ce.domains.api import get_datamimic_lib_version


class MountableApplication(Protocol):
    def mount(self, path: str, app: Starlette) -> None: ...


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Starlette, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        authorization = request.headers.get("authorization")
        scheme, separator, credentials = authorization.partition(" ") if authorization else ("", "", "")
        bearer = credentials if separator and scheme.casefold() == "bearer" else None
        token = bearer or request.headers.get("x-api-key")
        if token is None or not secrets.compare_digest(token, self.api_key):
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": "invalid_api_key"})
        return await call_next(request)


def create_server(
    *, workspace_root: Path | None = None, descriptor_path: PurePosixPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH
) -> FastMCP:
    server = FastMCP(name="datamimic-ce", version=None)
    root = workspace_root or Path.cwd()

    def application(path: PurePosixPath = descriptor_path) -> AuthoringApplication:
        return create_authoring_application(workspace_root=root, descriptor_path=path)

    @server.tool("datamimic_version")
    async def datamimic_version() -> dict[str, str]:
        """Show the installed CE package version."""
        version = await to_thread.run_sync(get_datamimic_lib_version)
        return {"ce_version": version or "unknown"}

    @server.tool("datamimic_schema")
    async def datamimic_schema(name: AuthoringSchemaId = AuthoringSchemaId.DM_JSON_DOCUMENT_V1) -> dict[str, JsonValue]:
        """Read one schema generated from the running Authoring contract."""
        return await to_thread.run_sync(application().schema, name)

    @server.tool("datamimic_capabilities")
    async def datamimic_capabilities(full: bool = False) -> dict[str, object]:
        """Discover CE runtime vocabulary; full includes each registered contract."""
        snapshot = await to_thread.run_sync(application().capabilities)
        return snapshot.to_dict() if full else snapshot.to_index_dict()

    @server.tool("datamimic_capability")
    async def datamimic_capability(domain: CapabilityDomain, name: str) -> CapabilityLookupResult:
        """Read one exact registered CE capability, or its typed not-found result."""
        return await to_thread.run_sync(application().capability, domain, name)

    @server.tool("datamimic_reference")
    async def datamimic_reference(request: ReferenceRequest) -> ReferenceResult:
        """Read one model-derived reference topic or named contract."""
        return await to_thread.run_sync(application().reference, request)

    @server.tool("datamimic_compile")
    async def datamimic_compile(request: CompileDocumentRequest) -> CompileDocumentResult:
        """Compile transient DM JSON to XML without claiming Build readiness."""
        return await to_thread.run_sync(application(request.descriptor_path).compile_document, request)

    @server.tool("datamimic_decompile")
    async def datamimic_decompile(request: DecompileDocumentRequest) -> DecompileDocumentResult:
        """Read persisted XML as transient DM JSON; proof declarations remain separate."""
        return await to_thread.run_sync(application(request.descriptor_path).decompile_document, request)

    @server.tool("datamimic_build")
    async def datamimic_build() -> BuildResult:
        """Prove the workspace project: its datamimic.xml entry against its acceptance/build.json."""
        return await to_thread.run_sync(application(PROJECT_ENTRY_PATH).build)

    @server.tool("datamimic_lint")
    async def datamimic_lint(request: LintRequest) -> LintResult:
        """Validate XML without executing it."""
        return await to_thread.run_sync(application().lint, request)

    @server.tool("datamimic_dry_run")
    async def datamimic_dry_run(request: RunRequest) -> RunResult:
        """Inspect bounded XML execution with write targets isolated."""
        return await to_thread.run_sync(application(request.descriptor_path).dry_run, request)

    @server.tool("datamimic_run")
    async def datamimic_run(request: RunRequest) -> RunResult:
        """Execute bounded XML; external writes require explicit allow_side_effects."""
        return await to_thread.run_sync(application(request.descriptor_path).run, request)

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
