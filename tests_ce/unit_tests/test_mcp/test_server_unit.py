"""Unit coverage for the MCP server wiring."""

from pathlib import Path

import pytest
from starlette.requests import Request
from starlette.responses import Response

from datamimic_ce.domains import facade
from datamimic_ce.mcp import resources
from datamimic_ce.mcp.models import GenerateArgs, ReferenceArgs, ScaffoldArgs
from datamimic_ce.mcp.server import (
    _APIKeyMiddleware,
    build_sse_app,
    create_server,
    generate_impl,
    list_domains_impl,
    reference_impl,
    scaffold_impl,
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


def test_reference_impl_projects_central_alias_rules() -> None:
    payload = reference_impl(ReferenceArgs(topic="element", name="iterate"))

    assert payload["ok"] is True
    assert "at least one of: source" in payload["content"]


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
        resources.load_schema("unknown", "v1", resources.SchemaKind.REQUEST)


def test_schema_document_validation_rejects_non_json_objects() -> None:
    with pytest.raises(TypeError, match="JSON object"):
        resources._validate_schema_document(["not", "an", "object"], Path("schema.json"))
    with pytest.raises(TypeError, match="JSON object"):
        resources._validate_schema_document({"invalid": {1, 2}}, Path("schema.json"))


def test_build_sse_app_applies_middleware() -> None:
    server = create_server(api_key="secret")
    middleware = server.http_middleware
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
    assert {entry.kind for entry in resources.iter_schema_resources()} == {
        resources.SchemaKind.REQUEST,
        resources.SchemaKind.RESPONSE,
    }


def test_scaffold_impl_valid_spec_dry_runs() -> None:
    """A valid spec from the scaffold test suite should render, lint clean, and dry-run."""
    spec = {
        "seed": 1,
        "generates": [{
            "name": "customers", "count": 30, "target": "JSON",
            "fields": [
                {"name": "id", "kind": "increment"},
                {"name": "full_name", "kind": "person_name"},
                {"name": "age", "kind": "int_range", "min": 18, "max": 90},
                {"name": "country", "kind": "weighted",
                 "values": ["US", "DE", "VN"], "weights": [0.5, 0.3, 0.2]},
            ],
        }],
    }
    args = ScaffoldArgs(spec=spec, max_count=30)
    result = scaffold_impl(args)

    assert result["ok"] is True
    assert result["stage"] == "acceptance"
    assert result["verified"] is True
    assert "xml" in result
    assert "products" in result
    assert isinstance(result["products"], list)
    assert len(result["products"]) > 0
    assert all("name" in p and "count" in p for p in result["products"])


def test_scaffold_impl_malformed_spec_render_error() -> None:
    """A malformed spec (missing generates) should fail at the render stage."""
    bad_spec = {}
    args = ScaffoldArgs(spec=bad_spec)
    result = scaffold_impl(args)

    assert result["ok"] is False
    assert result["stage"] == "render"
    assert "error" in result
    assert isinstance(result["error"], str)


def test_scaffold_args_reject_removed_lint_only_switch() -> None:
    """Scaffold always performs the canonical verification transaction."""
    spec = {
        "seed": 1,
        "generates": [{
            "name": "items", "count": 5, "target": "JSON",
            "fields": [{"name": "id", "kind": "increment"}],
        }],
    }
    with pytest.raises(ValueError, match="dry_run"):
        ScaffoldArgs(spec=spec, dry_run=False)
