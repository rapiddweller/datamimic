# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The project flow over a real stdio server: version, Build, run_project on checked-in tiny projects."""

import csv
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from tests_ce.mcp_stdio_fixtures import FIXTURES, stdio_client

pytest_plugins = ("tests_ce.mcp_stdio_fixtures",)

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport


@pytest.mark.anyio
async def test_build_then_run_project_writes_25_rows(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "customers"
    shutil.copytree(FIXTURES / "customers", project)
    launcher = tmp_path / "launcher"
    launcher.mkdir()
    async with stdio_client(launcher) as client:
        version = json.loads((await client.call_tool("datamimic_version", {})).content[0].text)
        assert version["build_protocol"] == "5.0"
        built = json.loads((await client.call_tool("datamimic_build", {"project": str(project)})).content[0].text)
        assert built["outcome"] == "ready"
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)})).content[0].text)
    assert run["outcome"] == "completed", run["log_tail"]
    csv_files = [item["path"] for item in run["artifacts"] if item["path"].endswith(".csv")]
    assert len(csv_files) == 1
    with (project / csv_files[0]).open(encoding="utf-8") as handle:
        assert len(list(csv.reader(handle))) == 26
    assert list(launcher.iterdir()) == []


@pytest.mark.anyio
async def test_database_project_is_not_run_without_allow_side_effects(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "warehouse"
    shutil.copytree(FIXTURES / "warehouse", project)
    before = sorted(path.name for path in project.rglob("*"))
    async with stdio_client(tmp_path) as client:
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)})).content[0].text)
    assert run["outcome"] == "not_run"
    assert {item["kind"] for item in run["required_side_effects"]} == {"database", "target"}
    assert sorted(path.name for path in project.rglob("*")) == before


@pytest.mark.anyio
async def test_rejected_build_is_returned_by_run_project(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "empty"
    project.mkdir()
    async with stdio_client(tmp_path) as client:
        run = json.loads((await client.call_tool("datamimic_run_project", {"project": str(project)})).content[0].text)
    assert run["outcome"] == "not_run" and run["build"]["outcome"] == "rejected"


@pytest.mark.anyio
async def test_unverified_sql_update_needs_both_confirmations(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "sql_update"
    shutil.copytree(FIXTURES / "sql_update", project)
    (project / "db").mkdir()
    database = project / "db" / "bank.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE bookings (id INTEGER PRIMARY KEY, amount_cents INTEGER)")
        connection.execute("INSERT INTO bookings VALUES (101, -1250)")

    def balance() -> int:
        with sqlite3.connect(database) as connection:
            return connection.execute("SELECT amount_cents FROM bookings WHERE id = 101").fetchone()[0]

    async with stdio_client(tmp_path) as client:
        normal = json.loads(
            (await client.call_tool("datamimic_run_project", {"project": str(project), "allow_side_effects": True}))
            .content[0]
            .text
        )
        assert normal["outcome"] == "not_run" and normal["not_run_reason"] == "build_rejected"
        assert any(item["code"] == "unsupported_bounded_operation" for item in normal["build"]["diagnostics"])
        for flags in ({}, {"confirm_unverified": True}, {"allow_side_effects": True}):
            refused = json.loads(
                (await client.call_tool("datamimic_run_project_unverified", {"project": str(project), **flags}))
                .content[0]
                .text
            )
            assert refused["outcome"] == "not_run" and refused["verification"] == "not_verified"
            assert balance() == -1250
        invalid = json.loads(
            (
                await client.call_tool(
                    "datamimic_run_project_unverified",
                    {
                        "project": str(project),
                        "confirm_unverified": True,
                        "allow_side_effects": True,
                        "timeout_seconds": 0,
                    },
                )
            )
            .content[0]
            .text
        )
        assert invalid["outcome"] == "not_run"
        assert "partially persisted" not in invalid["message"]
        assert balance() == -1250
        result = json.loads(
            (
                await client.call_tool(
                    "datamimic_run_project_unverified",
                    {"project": str(project), "confirm_unverified": True, "allow_side_effects": True},
                )
            )
            .content[0]
            .text
        )
    assert result["outcome"] == "completed", result
    assert result["verification"] == "not_verified"
    assert result["execution"]["exit_code"] == 0
    assert balance() == -1500


@pytest.mark.anyio
async def test_unverified_sql_failure_is_not_reported_as_success(anyio_backend: str, tmp_path: Path) -> None:
    project = tmp_path / "sql_update"
    shutil.copytree(FIXTURES / "sql_update", project)
    (project / "db").mkdir()
    async with stdio_client(tmp_path) as client:
        result = json.loads(
            (
                await client.call_tool(
                    "datamimic_run_project_unverified",
                    {"project": str(project), "confirm_unverified": True, "allow_side_effects": True},
                )
            )
            .content[0]
            .text
        )
    assert result["outcome"] == "failed"
    assert result["verification"] == "not_verified"
    assert result["execution"]["exit_code"] != 0


@pytest.mark.anyio
async def test_init_build_run_project_in_an_empty_project_and_a_second_init_refuses(
    anyio_backend: str, tmp_path: Path
) -> None:
    project = tmp_path / "shop"
    project.mkdir()
    launcher = tmp_path / "launcher"
    launcher.mkdir()
    async with stdio_client(launcher) as client:

        async def call(tool: str) -> dict:
            return json.loads((await client.call_tool(tool, {"project": str(project)})).content[0].text)

        init = await call("datamimic_init")
        assert init["outcome"] == "written"
        assert sorted(path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file()) == [
            "acceptance/build.json",
            "datamimic.xml",
        ]
        built = await call("datamimic_build")
        assert built["outcome"] == "ready"
        run = await call("datamimic_run_project")
        assert run["outcome"] == "completed", run["log_tail"]
        assert run["build_outcome"] == "ready"
        entry = (project / "datamimic.xml").read_bytes()
        second = await call("datamimic_init")
    assert second["outcome"] == "not_written"
    assert "these files exist already" in second["diagnostics"][0]["message"]
    assert (project / "datamimic.xml").read_bytes() == entry
    csv_files = [item["path"] for item in run["artifacts"] if item["path"].endswith(".csv")]
    assert csv_files and all(path.startswith("output/") for path in csv_files)
    for relative in csv_files:
        with (project / relative).open(encoding="utf-8") as handle:
            assert len(list(csv.reader(handle))) > 1
    assert list(launcher.iterdir()) == []
