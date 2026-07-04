from __future__ import annotations

# WHY: These tests prove CLI option parsing works without relying on Typer's
# Literal support. We validate behavior using Enums and avoid I/O by mocking.
#
# WHY monkeypatch names on the already-imported `datamimic_ce.mcp.cli` module
# instead of faking `sys.modules["datamimic_ce.mcp.server"]` before importing:
# `datamimic_ce.mcp.cli` binds `create_server`/`build_sse_app` at its own
# import time (`from datamimic_ce.mcp.server import ...`). If anything else in
# the test session has already imported `datamimic_ce.mcp.cli` (e.g. another
# test module doing `from datamimic_ce.mcp.cli import app`), that binding is
# already cached — re-importing via `sys.modules` substitution does not
# rebind it, and this test would silently start the real FastMCP server.
# Patching the names directly on the cached module is robust to import order.
from typer.testing import CliRunner

from datamimic_ce.mcp import cli as cli_mod

runner = CliRunner()


class _FakeServer:
    def __init__(self) -> None:
        self.runs: list[str] = []

    def run(self, mode: str) -> None:
        self.runs.append(mode)


def test_cli_transport_stdio_invokes_server_run(monkeypatch) -> None:
    fake = _FakeServer()

    monkeypatch.setattr(cli_mod, "create_server", lambda api_key=None: fake)
    monkeypatch.setattr(cli_mod, "HTTP_MIDDLEWARE_ATTR", "_datamimic_http_middleware")
    monkeypatch.setattr(cli_mod, "build_sse_app", lambda server, middleware: object())

    # Ensure uvicorn.run isn't called in stdio mode
    uvicorn_called = {"count": 0}

    def _fake_uvicorn_run(*args, **kwargs):  # noqa: ANN001
        uvicorn_called["count"] += 1

    monkeypatch.setattr(cli_mod.uvicorn, "run", _fake_uvicorn_run)

    result = runner.invoke(cli_mod.app, ["serve", "--transport", "stdio"])

    assert result.exit_code == 0, result.output
    assert fake.runs == ["stdio"]
    assert uvicorn_called["count"] == 0


def test_cli_transport_sse_invokes_uvicorn_with_params(monkeypatch) -> None:
    fake = _FakeServer()

    monkeypatch.setattr(cli_mod, "create_server", lambda api_key=None: fake)
    monkeypatch.setattr(cli_mod, "HTTP_MIDDLEWARE_ATTR", "_datamimic_http_middleware")
    monkeypatch.setattr(cli_mod, "build_sse_app", lambda server, middleware: object())

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
            "serve",
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
