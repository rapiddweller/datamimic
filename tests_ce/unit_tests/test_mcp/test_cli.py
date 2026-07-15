"""Transport option tests for the direct MCP CLI interface."""

from dataclasses import dataclass, field

from typer.testing import CliRunner

import datamimic_ce.mcp.cli as cli

runner = CliRunner()


@dataclass
class FakeServer:
    runs: list[str] = field(default_factory=list)

    def run(self, mode: str) -> None:
        self.runs.append(mode)


def test_stdio_is_a_direct_top_level_option(monkeypatch) -> None:
    server = FakeServer()
    uvicorn_calls: list[object] = []
    monkeypatch.setattr(cli, "create_server", lambda: server)
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: uvicorn_calls.append((args, kwargs)))

    result = runner.invoke(cli.app, ["--transport", "stdio"])

    assert result.exit_code == 0, result.output
    assert server.runs == ["stdio"]
    assert uvicorn_calls == []


def test_sse_is_a_direct_top_level_option(monkeypatch) -> None:
    server = FakeServer()
    application = object()
    captured: dict[str, object] = {}
    monkeypatch.setattr(cli, "create_server", lambda: server)
    monkeypatch.setattr(cli, "build_sse_app", lambda current, api_key: application)

    def record_run(app: object, host: str, port: int, log_level: str) -> None:
        captured.update(app=app, host=host, port=port, log_level=log_level)

    monkeypatch.setattr(cli.uvicorn, "run", record_run)
    result = runner.invoke(
        cli.app,
        ["--transport", "sse", "--host", "0.0.0.0", "--port", "1234", "--log-level", "debug"],
    )

    assert result.exit_code == 0, result.output
    assert server.runs == []
    assert captured == {
        "app": application,
        "host": "0.0.0.0",
        "port": 1234,
        "log_level": "debug",
    }


def test_serve_subcommand_does_not_exist() -> None:
    result = runner.invoke(cli.app, ["serve", "--transport", "stdio"])
    assert result.exit_code == 2
