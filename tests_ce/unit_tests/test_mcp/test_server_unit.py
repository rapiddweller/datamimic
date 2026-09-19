"""Unit tests for MCP transport wiring only."""

import pytest
from starlette.requests import Request
from starlette.responses import Response

from datamimic_ce.mcp.server import APIKeyMiddleware, build_sse_app, create_server


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


async def noop_app(scope: object, receive_call: object, send: object) -> None:
    return None


@pytest.mark.anyio
async def test_api_key_middleware_rejects_invalid_token(anyio_backend: str) -> None:
    middleware = APIKeyMiddleware(noop_app, "secret")
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []}, receive)

    async def call_next(_: Request) -> Response:
        return Response("ok")

    assert (await middleware.dispatch(request, call_next)).status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER"])
async def test_api_key_middleware_accepts_case_insensitive_bearer_scheme(
    anyio_backend: str, scheme: str
) -> None:
    middleware = APIKeyMiddleware(noop_app, "secret")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"authorization", f"{scheme} secret".encode())],
        },
        receive,
    )

    async def call_next(_: Request) -> Response:
        return Response("ok")

    assert (await middleware.dispatch(request, call_next)).status_code == 200


def test_build_sse_app_applies_optional_api_key_middleware() -> None:
    application = build_sse_app(create_server(), "secret")
    assert any(entry.cls is APIKeyMiddleware for entry in application.user_middleware)
