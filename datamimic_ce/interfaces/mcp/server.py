"""Optional MCP transport for the canonical authoring service."""

from __future__ import annotations

import json
import secrets
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path, PurePosixPath
from typing import Annotated, ParamSpec, Protocol, TypeVar

from anyio import to_thread
from dotenv import dotenv_values
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field, JsonValue
from pydantic_core import to_jsonable_python
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
    RejectedBuild,
    RejectedCompileDocument,
    RejectedDecompileDocument,
    RunPhase,
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


_P = ParamSpec("_P")
_R = TypeVar("_R")
MAX_RESULT_CHARACTERS = 60_000
_PROJECT_ARGUMENT = "Absolute path of the directory that holds datamimic.xml."


def _guarded(hint: str) -> Callable[[Callable[_P, Awaitable[_R]]], Callable[_P, Awaitable[_R]]]:
    """Refuse a result over the size limit and name the argument that narrows it."""

    def decorate(function: Callable[_P, Awaitable[_R]]) -> Callable[_P, Awaitable[_R]]:
        @wraps(function)
        async def guarded(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            result = await function(*args, **kwargs)
            # The text FastMCP sends: its default JSON form of the result.
            size = len(json.dumps(to_jsonable_python(result)))
            if size > MAX_RESULT_CHARACTERS:
                raise ToolError(json.dumps({"error": "result_too_large", "size": size, "hint": hint}))
            return result

        return guarded

    return decorate


def _project_root(project: str, workspace_root: Path | None) -> Path | str:
    """The resolved project directory, or the reason it cannot be used."""
    path = Path(project)
    if not path.is_absolute():
        return "project must be an absolute path."
    if not path.is_dir():
        return "project must be an existing directory."
    resolved = path.resolve()
    if workspace_root is not None and not resolved.is_relative_to(workspace_root.resolve()):
        return "project lies outside the workspace root of this server."
    return resolved


def create_server(
    *, workspace_root: Path | None = None, descriptor_path: PurePosixPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH
) -> FastMCP:
    """Serve the authoring tools; ``workspace_root`` only restricts which projects a call may name."""
    server = FastMCP(name="datamimic-ce", version=None)

    def application(root: Path, path: PurePosixPath = descriptor_path) -> AuthoringApplication:
        # The project's own .env reaches this call only; another project's call never sees it.
        environment = {name: value for name, value in dotenv_values(root / ".env").items() if value is not None}
        return create_authoring_application(workspace_root=root, descriptor_path=path, environment=environment)

    def tool(name: str, hint: str) -> Callable[[Callable[_P, Awaitable[_R]]], Callable[_P, Awaitable[_R]]]:
        """Register one tool whose result may not exceed the size limit."""

        def register(function: Callable[_P, Awaitable[_R]]) -> Callable[_P, Awaitable[_R]]:
            server.tool(name)(_guarded(hint)(function))
            return function

        return register

    def catalog_application() -> AuthoringApplication:
        return create_authoring_application()

    @tool("datamimic_version", "This result cannot be narrowed.")
    async def datamimic_version() -> dict[str, str]:
        """Show the installed CE package version and the Build protocol it speaks."""
        version = await to_thread.run_sync(get_datamimic_lib_version)
        return {"ce_version": version or "unknown", "build_protocol": catalog_application().build_protocol()}

    @tool("datamimic_schema", "Read a smaller schema: build_request_v5, expectation_intent, diagnostic, build_result.")
    async def datamimic_schema(name: AuthoringSchemaId = AuthoringSchemaId.DM_JSON_DOCUMENT_V1) -> dict[str, JsonValue]:
        """Read one schema generated from the running Authoring contract."""
        return await to_thread.run_sync(catalog_application().schema, name)

    @tool("datamimic_capabilities", "Call datamimic_capability with domain and name instead of the full list.")
    async def datamimic_capabilities() -> dict[str, object]:
        """Discover the names of the CE runtime vocabulary; read one contract with datamimic_capability."""
        snapshot = await to_thread.run_sync(catalog_application().capabilities)
        return snapshot.to_index_dict()

    @tool("datamimic_capability", "Name one exact capability; datamimic_capabilities lists the names.")
    async def datamimic_capability(domain: CapabilityDomain, name: str) -> CapabilityLookupResult:
        """Read one exact registered CE capability, or its typed not-found result."""
        return await to_thread.run_sync(catalog_application().capability, domain, name)

    @tool("datamimic_reference", "Set request.name to read one named contract instead of the whole topic.")
    async def datamimic_reference(request: ReferenceRequest) -> ReferenceResult:
        """Read one model-derived reference topic or named contract."""
        return await to_thread.run_sync(catalog_application().reference, request)

    @tool("datamimic_compile", "Compile a smaller DM JSON document.")
    async def datamimic_compile(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: CompileDocumentRequest
    ) -> CompileDocumentResult:
        """Compile transient DM JSON to XML without claiming Build readiness."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedCompileDocument.from_input_error(root)
        return await to_thread.run_sync(application(root, request.descriptor_path).compile_document, request)

    @tool("datamimic_decompile", "Decompile a smaller descriptor.")
    async def datamimic_decompile(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: DecompileDocumentRequest
    ) -> DecompileDocumentResult:
        """Read persisted XML as transient DM JSON; proof declarations remain separate."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedDecompileDocument.from_input_error(root)
        return await to_thread.run_sync(application(root, request.descriptor_path).decompile_document, request)

    @tool("datamimic_build", "Fix the first diagnostics and call datamimic_build again; read the artifacts on disk.")
    async def datamimic_build(project: Annotated[str, Field(description=_PROJECT_ARGUMENT)]) -> BuildResult:
        """Prove the project: its datamimic.xml entry against its acceptance/build.json."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedBuild.from_input_error(root)
        return await to_thread.run_sync(application(root, PROJECT_ENTRY_PATH).build)

    @tool("datamimic_lint", "Lint a smaller descriptor; split the model into included steps.")
    async def datamimic_lint(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: LintRequest
    ) -> LintResult:
        """Validate XML without executing it."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return LintResult.from_input_error(root)
        return await to_thread.run_sync(application(root).lint, request)

    @tool("datamimic_dry_run", "Lower sample_rows or max_count.")
    async def datamimic_dry_run(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: RunRequest
    ) -> RunResult:
        """Inspect bounded XML execution with write targets isolated."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RunResult.from_input_error(root).model_copy(update={"phase": RunPhase.DRY_RUN})
        return await to_thread.run_sync(application(root, request.descriptor_path).dry_run, request)

    @tool("datamimic_run", "Lower sample_rows or max_count.")
    async def datamimic_run(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: RunRequest
    ) -> RunResult:
        """Execute bounded XML; external writes require explicit allow_side_effects."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RunResult.from_input_error(root)
        return await to_thread.run_sync(application(root, request.descriptor_path).run, request)

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
