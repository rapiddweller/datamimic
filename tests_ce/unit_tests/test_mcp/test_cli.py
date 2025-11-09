from __future__ import annotations

# WHY: These tests prove CLI option parsing works without relying on Typer's
# Literal support. We validate behavior using Enums and avoid I/O by mocking.

from importlib import import_module
from types import ModuleType
from typer.testing import CliRunner


runner = CliRunner()


class _FakeServer:
    def __init__(self) -> None:
        self.runs: list[str] = []

    def run(self, mode: str) -> None:
        self.runs.append(mode)


def test_cli_transport_stdio_invokes_server_run(monkeypatch) -> None:
    fake = _FakeServer()

    # Install a fake server module before importing the CLI to avoid optional deps
    fake_server = ModuleType("datamimic_ce.mcp.server")
    fake_server.HTTP_MIDDLEWARE_ATTR = "_datamimic_http_middleware"  # type: ignore[attr-defined]

    def _fake_create_server(api_key=None):  # noqa: ANN001
        return fake

    def _fake_build_sse_app(server, middleware):  # noqa: ANN001
        return object()

    fake_server.create_server = _fake_create_server  # type: ignore[attr-defined]
    fake_server.build_sse_app = _fake_build_sse_app  # type: ignore[attr-defined]
    fake_server.mount_mcp = lambda *a, **k: None  # type: ignore[attr-defined]

    monkeypatch.setitem(
        __import__("sys").modules,
        "datamimic_ce.mcp.server",
        fake_server,
    )

    cli_mod = import_module("datamimic_ce.mcp.cli")

    # Ensure uvicorn.run isn't called in stdio mode
    uvicorn_called = {"count": 0}

    def _fake_uvicorn_run(*args, **kwargs):  # noqa: ANN001
        uvicorn_called["count"] += 1

    monkeypatch.setattr(cli_mod.uvicorn, "run", _fake_uvicorn_run)

    result = runner.invoke(cli_mod.app, ["--transport", "stdio"])

    assert result.exit_code == 0, result.output
    assert fake.runs == ["stdio"]
    assert uvicorn_called["count"] == 0


def test_cli_transport_sse_invokes_uvicorn_with_params(monkeypatch) -> None:
    fake = _FakeServer()

    # Install a fake server module before importing the CLI to avoid optional deps
    fake_server = ModuleType("datamimic_ce.mcp.server")
    fake_server.HTTP_MIDDLEWARE_ATTR = "_datamimic_http_middleware"  # type: ignore[attr-defined]

    def _fake_create_server(api_key=None):  # noqa: ANN001
        return fake

    def _fake_build_sse_app(server, middleware):  # noqa: ANN001
        return object()

    fake_server.create_server = _fake_create_server  # type: ignore[attr-defined]
    fake_server.build_sse_app = _fake_build_sse_app  # type: ignore[attr-defined]
    fake_server.mount_mcp = lambda *a, **k: None  # type: ignore[attr-defined]

    monkeypatch.setitem(
        __import__("sys").modules,
        "datamimic_ce.mcp.server",
        fake_server,
    )

    cli_mod = import_module("datamimic_ce.mcp.cli")

    captured = {}

    def _fake_uvicorn_run(app, host, port, log_level):  # noqa: ANN001
        captured.update({
            "app": app,
            "host": host,
            "port": port,
            "log_level": log_level,
        })

    monkeypatch.setattr(cli_mod.uvicorn, "run", _fake_uvicorn_run)

    result = runner.invoke(
        cli_mod.app,
        [
            "--transport",
            "sse",
            "--host",
            "0.0.0.0",
            "--port",
            "1234",
            "--log-level",
            "debug",
        ],
    )

    assert result.exit_code == 0, result.output
    # server.run should not be used for SSE
    assert fake.runs == []
    # uvicorn.run should receive our params, including mapped log level
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 1234
    assert captured["log_level"] == "debug"
