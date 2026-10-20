"""Transport option tests for the direct MCP CLI interface."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from typer.testing import CliRunner

import datamimic_ce.interfaces.mcp.cli as cli
from datamimic_ce.interfaces.mcp import server as mcp_server

runner = CliRunner()


@dataclass
class FakeServer:
    runs: list[str] = field(default_factory=list)

    def run(self, mode: str) -> None:
        self.runs.append(mode)


def test_stdio_is_a_direct_top_level_option(monkeypatch) -> None:
    server = FakeServer()
    uvicorn_calls: list[object] = []
    monkeypatch.setattr(mcp_server, "create_server", lambda *, workspace_root=None: server)
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: uvicorn_calls.append((args, kwargs)))

    result = runner.invoke(cli.app, ["--transport", "stdio"])

    assert result.exit_code == 0, result.output
    assert server.runs == ["stdio"]
    assert uvicorn_calls == []


def test_sse_is_a_direct_top_level_option(monkeypatch) -> None:
    server = FakeServer()
    application = object()
    captured: dict[str, object] = {}
    monkeypatch.setattr(mcp_server, "create_server", lambda *, workspace_root=None: server)
    monkeypatch.setattr(mcp_server, "build_sse_app", lambda current, api_key: application)

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


@pytest.mark.parametrize("transport", ["stdio", "sse"])
def test_explicit_workspace_root_is_independent_of_launcher_directory(
    monkeypatch, tmp_path: Path, transport: str
) -> None:
    project = tmp_path / "project with spaces"
    launcher = tmp_path / "launcher"
    project.mkdir()
    launcher.mkdir()
    monkeypatch.chdir(launcher)
    roots: list[Path | None] = []
    server = FakeServer()

    def create_server(*, workspace_root: Path | None = None) -> FakeServer:
        roots.append(workspace_root)
        return server

    monkeypatch.setattr(mcp_server, "create_server", create_server)
    monkeypatch.setattr(mcp_server, "build_sse_app", lambda current, api_key: object())
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: None)
    result = runner.invoke(cli.app, ["--transport", transport, "--workspace-root", str(project)])

    assert result.exit_code == 0, result.output
    assert roots == [project.resolve()]
    assert Path.cwd() == launcher


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_workspace_root_requires_an_existing_directory(tmp_path: Path, kind: str) -> None:
    path = tmp_path / kind
    if kind == "file":
        path.write_text("not a directory")
    result = runner.invoke(cli.app, ["--transport", "stdio", "--workspace-root", str(path)])
    assert result.exit_code == 2, result.output
