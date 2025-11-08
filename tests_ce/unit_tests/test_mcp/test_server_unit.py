"""Unit coverage for the MCP server wiring."""

import pytest
from starlette.requests import Request
from starlette.responses import Response

from datamimic_ce.domains import facade
from datamimic_ce.mcp import resources
from datamimic_ce.mcp.models import GenerateArgs
from datamimic_ce.mcp.server import (
    HTTP_MIDDLEWARE_ATTR,
    build_sse_app,
    create_server,
    generate_impl,
    list_domains_impl,
    _APIKeyMiddleware,
)


@pytest.fixture
def anyio_backend() -> str:  # pragma: no cover - fixture glue
    return "asyncio"


async def _receive() -> dict:
    return {"type": "http.request", "body": b"", "more_body": False}


async def _noop_app(scope, receive, send):  # pragma: no cover - helper
    return None


def test_list_domains_matches_registry() -> None:
    listing = list_domains_impl()
    registry_keys = set(facade.REGISTRY.keys())
    reported_keys = {(item["domain"], item["version"]) for item in listing}
    assert reported_keys == registry_keys


def test_generate_impl_forwards_payload(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_generate(payload):
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(facade, "generate_domain", fake_generate)

    args = GenerateArgs(domain="person", locale="en_US", seed=123, count=2)
    result = generate_impl(args)

    assert result == {"ok": True}
    forwarded = captured["payload"]
    assert forwarded["domain"] == "person"
    assert forwarded["seed"] == 123
    assert forwarded["count"] == 2
    assert forwarded["locale"] == "en_US"


@pytest.mark.anyio
async def test_api_key_middleware_rejects_invalid_token(anyio_backend) -> None:
    middleware = _APIKeyMiddleware(_noop_app, "secret")
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    request = Request(scope, _receive)

    async def call_next(_: Request) -> Response:  # pragma: no cover - defensive
        return Response("ok")

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_api_key_middleware_allows_matching_bearer(anyio_backend) -> None:
    middleware = _APIKeyMiddleware(_noop_app, "secret")
    headers = [(b"authorization", b"Bearer secret")]
    scope = {"type": "http", "method": "GET", "path": "/", "headers": headers}
    request = Request(scope, _receive)

    async def call_next(_: Request) -> Response:
        return Response("ok", status_code=200)

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 200


def test_missing_schema_raises() -> None:
    with pytest.raises(FileNotFoundError):
        resources.load_schema("unknown", "v1", "request")


def test_build_sse_app_applies_middleware() -> None:
    server = create_server(api_key="secret")
    middleware = getattr(server, HTTP_MIDDLEWARE_ATTR)
    assert middleware is not None
    sse_app = build_sse_app(server, middleware)
    assert any(entry.cls is _APIKeyMiddleware for entry in sse_app.user_middleware)


def test_schema_resources_loadable() -> None:
    discovered: list[str] = []
    for entry in resources.iter_schema_resources():
        discovered.append(entry.uri)
        loaded = resources.load_schema(entry.domain, entry.version, entry.kind)
        assert isinstance(loaded, dict)
        assert loaded, "Schema should not be empty"
    assert discovered, "Expected packaged schema resources"
