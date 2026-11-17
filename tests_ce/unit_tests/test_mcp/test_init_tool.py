"""`datamimic_init`: the CLI's `authoring init` over MCP, with the same refusals and never an overwrite."""

import json
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
Client = fastmcp_client.Client

import datamimic_ce.interfaces.mcp.server as mcp_server  # noqa: E402
from datamimic_ce.authoring import create_authoring_application  # noqa: E402
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild  # noqa: E402
from datamimic_ce.interfaces.mcp.server import create_server  # noqa: E402

STARTER_FILES = ["acceptance/build.json", "datamimic.xml"]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def call_init(project: str, workspace_root: Path | None = None, **arguments: str) -> dict:
    async with Client(create_server(workspace_root=workspace_root)) as client:
        response = await client.call_tool("datamimic_init", {"project": project, **arguments})
    return json.loads(response.content[0].text)


def files_of(project: Path) -> list[str]:
    return sorted(path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file())


@pytest.mark.anyio
async def test_init_requires_project_and_offers_the_pattern(anyio_backend: str) -> None:
    async with Client(create_server()) as client:
        tool = next(tool for tool in await client.list_tools() if tool.name == "datamimic_init")
    assert tool.inputSchema["required"] == ["project"]
    assert set(tool.inputSchema["properties"]) == {"project", "pattern"}


@pytest.mark.anyio
async def test_init_writes_the_starter_that_build_proves_ready(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "shop"
    project.mkdir()

    result = await call_init(str(project))

    assert result["outcome"] == "written"
    assert result["pattern"] == "flat"
    assert result["files"] == ["datamimic.xml", "acceptance/build.json"]
    assert files_of(project) == STARTER_FILES
    built = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, ReadyBuild) and not built.coverage.has_gaps


@pytest.mark.anyio
async def test_init_creates_a_missing_project_directory_like_the_cli(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "a" / "b"

    result = await call_init(str(project), workspace_root=tmp_path)

    assert result["outcome"] == "written"
    assert files_of(project) == STARTER_FILES


@pytest.mark.anyio
@pytest.mark.parametrize("existing", ["datamimic.xml", "acceptance/build.json"])
async def test_init_never_overwrites_and_writes_nothing(anyio_backend: str, tmp_path: Path, existing: str) -> None:
    (tmp_path / existing).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / existing).write_text("mine", encoding="utf-8")
    before = files_of(tmp_path)

    result = await call_init(str(tmp_path))

    assert result["outcome"] == "not_written"
    assert result["files"] == []
    assert result["diagnostics"][0]["code"] == "input"
    assert f"these files exist already: {existing}" in result["diagnostics"][0]["message"]
    assert files_of(tmp_path) == before
    assert (tmp_path / existing).read_text(encoding="utf-8") == "mine"


@pytest.mark.anyio
async def test_a_symlinked_project_directory_is_refused(anyio_backend: str, tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    result = await call_init(str(link))

    assert result["outcome"] == "not_written"
    assert "symlink" in result["diagnostics"][0]["message"]
    assert list(real.iterdir()) == []


@pytest.mark.anyio
async def test_a_symlinked_target_inside_the_project_is_refused(anyio_backend: str, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "p"
    project.mkdir()
    (project / "acceptance").symlink_to(outside, target_is_directory=True)

    result = await call_init(str(project))

    assert result["outcome"] == "not_written"
    assert "acceptance is a symlink; nothing written" in result["diagnostics"][0]["message"]
    assert list(outside.iterdir()) == []
    assert not (project / PROJECT_ENTRY_PATH).exists()


@pytest.mark.anyio
async def test_a_file_as_project_is_refused(anyio_backend: str, tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("x", encoding="utf-8")

    result = await call_init(str(target))

    assert result["outcome"] == "not_written"
    assert "not a directory" in result["diagnostics"][0]["message"]


@pytest.mark.anyio
async def test_a_relative_project_is_refused_and_writes_nothing(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = await call_init("relative-shop")

    assert result["outcome"] == "not_written"
    assert result["diagnostics"][0]["code"] == "input"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.anyio
async def test_a_project_outside_the_workspace_root_is_refused(anyio_backend: str, tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"

    for project in (outside, allowed / ".." / "outside"):
        result = await call_init(str(project), workspace_root=allowed)
        assert result["outcome"] == "not_written"
        assert result["diagnostics"][0]["code"] == "input"
        assert not outside.exists()
        assert str(tmp_path) not in json.dumps(result)


@pytest.mark.anyio
async def test_init_result_is_guarded_by_the_size_limit(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mcp_server, "MAX_RESULT_CHARACTERS", 10)
    async with Client(create_server()) as client:
        with pytest.raises(Exception, match="result_too_large"):
            await client.call_tool("datamimic_init", {"project": str(tmp_path)})


@pytest.mark.anyio
async def test_init_reports_write_oserror_and_files_written_so_far(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datamimic_ce.authoring.adapters import workspace

    write_file = workspace._write_file
    calls = 0

    def fail_second(path: Path, content: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk full")
        write_file(path, content)

    monkeypatch.setattr(workspace, "_write_file", fail_second)
    result = await call_init(str(tmp_path))
    assert result["outcome"] == "not_written"
    message = result["diagnostics"][0]["message"]
    assert "disk full" in message and "acceptance/build.json" in message and "datamimic.xml" in message


@pytest.mark.anyio
async def test_init_names_a_file_that_may_be_partial_after_write_error(
    anyio_backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.write_text

    def fail_after_open(path: Path, data: str, *args, **kwargs) -> int:
        written = original(path, data, *args, **kwargs)
        if path.name == "build.json":
            raise OSError("disk full")
        return written

    monkeypatch.setattr(Path, "write_text", fail_after_open)
    result = await call_init(str(tmp_path))
    assert result["outcome"] == "not_written"
    message = result["diagnostics"][0]["message"]
    assert "acceptance/build.json" in message and "may be partial" in message
