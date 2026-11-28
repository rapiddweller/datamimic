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
from fastmcp.exceptions import ValidationError as ToolValidationError
from fastmcp.tools import FunctionTool, ToolResult
from pydantic import Field, JsonValue, StrictBool, ValidationError
from pydantic_core import to_json, to_jsonable_python
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from datamimic_ce.authoring import AuthoringApplication, create_authoring_application
from datamimic_ce.authoring.adapters.workspace import init_project
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain, CapabilityLookupResult, RuntimeVersion
from datamimic_ce.authoring.domain.project_run import (
    ProjectParam,
    ProjectRunRequest,
    ProjectRunResult,
    UnverifiedProjectRunResult,
)
from datamimic_ce.authoring.domain.project_scaffold import ProjectInitResult, ProjectPattern
from datamimic_ce.authoring.domain.reference import ReferenceLookupResult
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
from mcp.types import TextContent


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
_XML_ARGUMENT_EXAMPLE = '{"project": "/absolute/project", "xml": "<setup/>"}'


def _guarded(function: Callable[_P, Awaitable[_R]], hint: str) -> Callable[_P, Awaitable[ToolResult]]:
    """Refuse a result over the size limit and name the argument that narrows it."""

    @wraps(function)
    async def guarded(*args: _P.args, **kwargs: _P.kwargs) -> ToolResult:
        result = await function(*args, **kwargs)
        # FastMCP 4 serializes JSON compactly, without ASCII escaping.
        encoded: bytes = to_json(to_jsonable_python(result))
        text = str(encoded, "utf-8")
        size = len(text)
        if size > MAX_RESULT_CHARACTERS:
            raise ToolError(json.dumps({"error": "result_too_large", "size": size, "hint": hint}))
        return ToolResult(content=[TextContent(type="text", text=text)])

    return guarded


class _CompatibleRequestTool(FunctionTool):
    """Advertise flat arguments and adapt them to the existing typed request."""

    flat_example: str = ""

    async def run(self, arguments: dict[str, JsonValue]) -> ToolResult:
        project = (
            {"project": arguments["project"]}
            if "project" in self.parameters["properties"] and "project" in arguments
            else {}
        )
        request = {key: arguments[key] for key in arguments if key not in project}
        if "request" in request and len(request) != 1:
            raise ToolValidationError(f"Do not mix flat arguments with request. Use {self.flat_example}.")
        wrapped = request if "request" in request else {"request": request}
        try:
            return await super().run({**project, **wrapped})
        except ToolValidationError as exc:
            raise ToolValidationError(f"Invalid arguments. Use {self.flat_example}.") from exc


def _compatible_tool(function: Callable[_P, Awaitable[ToolResult]], name: str, flat_example: str) -> FunctionTool:
    tool = _CompatibleRequestTool.from_function(function, name=name, output_schema=None)
    assert isinstance(tool, _CompatibleRequestTool)
    tool.flat_example = flat_example
    schema = tool.parameters
    properties = schema["properties"]
    request = properties["request"]
    # FastMCP can inline the request model or keep it in Pydantic's local $defs.
    reference_prefix = "#/$defs/"
    request_model = schema["$defs"][request["$ref"][len(reference_prefix) :]] if "$ref" in request else request
    request_model = {"required": [], **request_model}
    fields = request_model["properties"]
    schema["required"] = [field for field in schema["required"] if field != "request"]
    schema["properties"] = {
        **properties,
        **fields,
        "request": {**request, "deprecated": True, "description": "Legacy wrapper for one release."},
    }
    schema["additionalProperties"] = False
    schema["oneOf"] = [
        {
            "title": "Preferred: flat arguments",
            "required": request_model["required"],
            "not": {"required": ["request"]},
        },
        {"title": "Legacy: request wrapper", "required": ["request"], "properties": {field: False for field in fields}},
    ]
    tool.description = f"{tool.description} Prefer flat arguments: {flat_example}. The request wrapper is deprecated."
    return tool


def _project_root(project: str, workspace_root: Path | None, *, new: bool = False) -> Path | str:
    """The project directory, or the reason it cannot be used; a new project need not exist and keeps its own path."""
    path = Path(project)
    if not path.is_absolute():
        return "project must be an absolute path."
    if not new and not path.is_dir():
        return "project must be an existing directory."
    resolved = path.resolve()
    if workspace_root is not None and not resolved.is_relative_to(workspace_root.resolve()):
        return "project lies outside the workspace root of this server."
    return path if new else resolved


def create_server(
    *,
    workspace_root: Path | None = None,
    descriptor_path: PurePosixPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH,
    enable_unverified_run: bool = False,
) -> FastMCP:
    """Serve the authoring tools; ``workspace_root`` only restricts which projects a call may name."""
    server = FastMCP(name="datamimic-ce", version=None)

    def application(root: Path, path: PurePosixPath = descriptor_path) -> AuthoringApplication:
        # The project's own .env reaches this call only; another project's call never sees it.
        environment = {name: value for name, value in dotenv_values(root / ".env").items() if value is not None}
        return create_authoring_application(workspace_root=root, descriptor_path=path, environment=environment)

    def tool(
        name: str, hint: str, *, flat_example: str | None = None
    ) -> Callable[[Callable[_P, Awaitable[_R]]], Callable[_P, Awaitable[_R]]]:
        """Register one tool whose result may not exceed the size limit."""

        def register(function: Callable[_P, Awaitable[_R]]) -> Callable[_P, Awaitable[_R]]:
            guarded = _guarded(function, hint)
            definition = (
                FunctionTool.from_function(guarded, name=name, output_schema=None)
                if flat_example is None
                else _compatible_tool(guarded, name, flat_example)
            )
            server.add_tool(definition)
            return function

        return register

    def catalog_application() -> AuthoringApplication:
        return create_authoring_application()

    @tool("datamimic_version", "This result cannot be narrowed.")
    async def datamimic_version() -> RuntimeVersion:
        """Show the installed CE package version, Python version, git commit (git install only) and Build protocol."""
        return await to_thread.run_sync(catalog_application().version)

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

    @tool(
        "datamimic_reference",
        "Set name to read one named contract instead of the whole topic.",
        flat_example='{"topic": "assembly", "name": "starter"}',
    )
    async def datamimic_reference(request: ReferenceRequest) -> ReferenceLookupResult:
        """Read one model-derived reference topic or named contract, or its typed not-found result."""
        return await to_thread.run_sync(catalog_application().reference, request)

    @tool(
        "datamimic_compile",
        "Compile a smaller DM JSON document.",
        flat_example='{"project": "/absolute/project", "document": {"root": {"kind": "setup"}}}',
    )
    async def datamimic_compile(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: CompileDocumentRequest
    ) -> CompileDocumentResult:
        """Compile transient DM JSON to XML without claiming Build readiness."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedCompileDocument.from_input_error(root)
        return await to_thread.run_sync(application(root, request.descriptor_path).compile_document, request)

    @tool("datamimic_decompile", "Decompile a smaller descriptor.", flat_example=_XML_ARGUMENT_EXAMPLE)
    async def datamimic_decompile(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: DecompileDocumentRequest
    ) -> DecompileDocumentResult:
        """Read persisted XML as transient DM JSON; proof declarations remain separate."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedDecompileDocument.from_input_error(root)
        return await to_thread.run_sync(application(root, request.descriptor_path).decompile_document, request)

    @tool("datamimic_init", "This result cannot be narrowed.")
    async def datamimic_init(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)],
        pattern: ProjectPattern = ProjectPattern.FLAT,
    ) -> ProjectInitResult:
        """Write a starter project (datamimic.xml and acceptance/build.json) that Build accepts. Never overwrites."""
        root = _project_root(project, workspace_root, new=True)
        if isinstance(root, str):
            return ProjectInitResult.from_input_error(root)
        scaffold = await to_thread.run_sync(catalog_application().scaffold, pattern)
        return await to_thread.run_sync(init_project, root, scaffold)

    @tool("datamimic_build", "Fix the first diagnostics and call datamimic_build again; read the artifacts on disk.")
    async def datamimic_build(project: Annotated[str, Field(description=_PROJECT_ARGUMENT)]) -> BuildResult:
        """Prove the project: its datamimic.xml entry against its acceptance/build.json."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RejectedBuild.from_input_error(root)
        return await to_thread.run_sync(application(root, PROJECT_ENTRY_PATH).build)

    @tool("datamimic_run_project", "Read the generated files from disk; the result lists their paths.")
    async def datamimic_run_project(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)],
        allow_side_effects: bool = False,
        params: dict[str, str] | None = None,
        timeout_seconds: int = 600,
    ) -> ProjectRunResult:
        """Build the project, then run it for its real data. Targets outside the project need allow_side_effects."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return ProjectRunResult.from_input_error(root)
        values: dict[str, str] = params or {}
        try:
            request = ProjectRunRequest(
                allow_side_effects=allow_side_effects,
                params=tuple(ProjectParam(name=name, value=values[name]) for name in values),
                timeout_seconds=timeout_seconds,
            )
        except ValidationError:
            return ProjectRunResult.from_input_error("Run options are invalid: check params and timeout_seconds.")
        return await to_thread.run_sync(application(root, PROJECT_ENTRY_PATH).run_project, request)

    async def datamimic_run_project_unverified(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)],
        confirm_unverified: StrictBool = False,
        allow_side_effects: StrictBool = False,
        params: dict[str, str] | None = None,
        timeout_seconds: int = 600,
    ) -> UnverifiedProjectRunResult:
        """Run without Build or acceptance checks. Require user approval for all effects, including partial effects."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return UnverifiedProjectRunResult(outcome="not_run", message=root)
        values = params or {}
        try:
            request = ProjectRunRequest(
                allow_side_effects=allow_side_effects,
                params=tuple(ProjectParam(name=name, value=values[name]) for name in values),
                timeout_seconds=timeout_seconds,
            )
        except ValidationError:
            return UnverifiedProjectRunResult(outcome="not_run", message="Run options are invalid.")
        result = await to_thread.run_sync(
            application(root, PROJECT_ENTRY_PATH).run_project_unverified, request, confirm_unverified
        )
        if result.execution is not None and len(to_json(to_jsonable_python(result))) > MAX_RESULT_CHARACTERS - 10_000:
            execution = result.execution.model_copy(update={"log_tail": (), "artifacts": ()})
            result = result.model_copy(update={"execution": execution, "details_truncated": True})
        return result

    if enable_unverified_run:
        tool("datamimic_run_project_unverified", "Inspect the run result and verify its effects independently.")(
            datamimic_run_project_unverified
        )

    @tool(
        "datamimic_lint",
        "Lint a smaller descriptor; split the model into included steps.",
        flat_example=_XML_ARGUMENT_EXAMPLE,
    )
    async def datamimic_lint(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: LintRequest
    ) -> LintResult:
        """Validate XML without executing it."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return LintResult.from_input_error(root)
        return await to_thread.run_sync(application(root).lint, request)

    @tool("datamimic_dry_run", "Lower sample_rows or max_count.", flat_example=_XML_ARGUMENT_EXAMPLE)
    async def datamimic_dry_run(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: RunRequest
    ) -> RunResult:
        """Inspect bounded XML execution with write targets isolated."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RunResult.from_input_error(root, RunPhase.DRY_RUN)
        return await to_thread.run_sync(application(root, request.descriptor_path).dry_run, request)

    @tool("datamimic_run", "Lower sample_rows or max_count.", flat_example=_XML_ARGUMENT_EXAMPLE)
    async def datamimic_run(
        project: Annotated[str, Field(description=_PROJECT_ARGUMENT)], request: RunRequest
    ) -> RunResult:
        """Execute bounded XML; external writes require explicit allow_side_effects."""
        root = _project_root(project, workspace_root)
        if isinstance(root, str):
            return RunResult.from_input_error(root, RunPhase.RUN)
        return await to_thread.run_sync(application(root, request.descriptor_path).run, request)

    return server


def build_sse_app(server: FastMCP, api_key: str | None = None) -> Starlette:
    application = server.http_app(path="/sse", transport="sse")
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
