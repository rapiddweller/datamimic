"""FastMCP server wiring for DataMimic domains."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import MISSING, fields
from typing import TYPE_CHECKING, Any, cast

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from datamimic_ce.domains import facade
from datamimic_ce.mcp import resources
from datamimic_ce.mcp.models import GenerateArgs

if TYPE_CHECKING:  # pragma: no cover - import hint for typing only
    from typing import Protocol

    class _FastAPILike(Protocol):  # pylint: disable=too-few-public-methods
        def mount(self, path: str, app: Any) -> None:
            """Mount an ASGI app at the provided path."""
else:  # pragma: no cover - runtime fallback avoids optional FastAPI dependency
    _FastAPILike = Any


HTTP_MIDDLEWARE_ATTR = "_datamimic_http_middleware"


class _APIKeyMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Reject requests that lack the configured API key."""

    def __init__(self, app: Any, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        provided = request.headers.get("authorization")
        token = None
        if provided and provided.lower().startswith("bearer "):
            token = provided.split(" ", 1)[1]
        if token is None:
            token = request.headers.get("x-api-key")
        if token != self._api_key:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_api_key"},
            )
        return await call_next(request)


def list_domains_impl() -> list[dict[str, Any]]:
    """Return metadata describing the registered domain generators."""

    catalog: list[dict[str, Any]] = []
    for (domain, version), (request_cls, _) in sorted(facade.REGISTRY.items()):
        defaults: dict[str, Any] = {}
        field_names: list[str] = []
        for field in fields(request_cls):
            if field.name == "request_hash":
                continue
            field_names.append(field.name)
            if field.default is not MISSING:
                defaults[field.name] = field.default
        catalog.append(
            {
                "domain": domain,
                "version": version,
                "request_fields": field_names,
                "defaults": defaults,
            }
        )
    return catalog


def generate_impl(args: GenerateArgs) -> dict[str, Any]:
    """Delegate to the domain facade with deterministic payloads."""

    payload = args.to_payload()
    # WHY: The facade owns canonical hashing and RNG seeding; forwarding the payload
    # untouched prevents duplicate hash derivations and keeps determinism obvious.
    return facade.generate_domain(payload)


def create_server(*, api_key: str | None = None) -> FastMCP:
    """Create a FastMCP server exposing DataMimic generators."""

    server = FastMCP(
        name="datamimic-ce",
        version=None,
    )

    @server.tool("list_domains")
    async def list_domains() -> list[dict[str, Any]]:
        return list_domains_impl()

    @server.tool("generate")
    async def generate(args: GenerateArgs) -> dict[str, Any]:
        return generate_impl(args)

    http_middleware = _build_http_middleware(api_key)
    setattr(server, HTTP_MIDDLEWARE_ATTR, http_middleware)

    for schema in resources.iter_schema_resources():
        loader = _schema_loader(schema.domain, schema.version, schema.kind)
        server.resource(schema.uri, mime_type="application/schema+json")(loader)

    return server


def mount_mcp(
    app: _FastAPILike,
    *,
    path: str = "/mcp",
    api_key: str | None = None,
    server: FastMCP | None = None,
) -> FastMCP:
    """Mount the FastMCP server onto an existing FastAPI application."""

    mcp_server = server or create_server(api_key=api_key)
    http_middleware = getattr(mcp_server, HTTP_MIDDLEWARE_ATTR, None)
    sse_app = build_sse_app(mcp_server, http_middleware)
    app.mount(path, sse_app)
    return mcp_server


def _build_http_middleware(api_key: str | None) -> list[Middleware] | None:
    if not api_key:
        return None
    # WHY: Starlette middleware keeps HTTP transports gated.
    # Avoid reimplementing FastMCP internals just for header inspection.
    return [Middleware(_APIKeyMiddleware, api_key=api_key)]


def _schema_loader(
    domain: str,
    version: str,
    kind: resources.SchemaKind,
) -> Callable[[], dict[str, Any]]:
    """Build a parameterless schema loader for the FastMCP registry."""

    def load() -> dict[str, Any]:
        return resources.load_schema(domain, version, kind)

    return load


def build_sse_app(
    server: FastMCP,
    middleware: list[Middleware] | None,
) -> Starlette:
    """Create an SSE ASGI app with optional middleware layering.

    Note: FastMCP's Starlette route may log a benign TypeError due to returning
    None after streaming. This does not affect functionality; tests verify end-to-end.
    """

    sse_factory = cast(Callable[[], Starlette], server.sse_app)
    sse_app = sse_factory()
    if middleware:
        for entry in middleware:
            # WHY: Starlette stores middleware callables and kwargs separately; rehydrate
            # them instead of reimplementing the wrapping logic here.
            sse_app.add_middleware(entry.cls, *entry.args, **entry.kwargs)
    return sse_app


__all__ = [
    "create_server",
    "mount_mcp",
    "generate_impl",
    "list_domains_impl",
    "build_sse_app",
]
