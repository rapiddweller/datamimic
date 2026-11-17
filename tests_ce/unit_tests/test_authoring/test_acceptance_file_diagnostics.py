# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A malformed acceptance/build.json is reported against that file, in every transport (#545)."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    BuildResult,
    RejectedBuild,
)
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import write_project

_FILE = PROJECT_ACCEPTANCE_PATH.as_posix()
_XML = '<setup rngSeed="7"><generate name="rows" count="2"><key name="id" generator="IncrementGenerator"/></generate></setup>'
_COUNT = {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}


def _build(root: Path, acceptance: str) -> RejectedBuild:
    write_project(root, _XML)
    (root / PROJECT_ACCEPTANCE_PATH).write_text(acceptance, encoding="utf-8")
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def test_json_syntax_error_names_the_file_with_line_and_column(tmp_path: Path) -> None:
    [diagnostic] = _build(tmp_path, "{oops").diagnostics

    assert diagnostic.path == (_FILE,)
    assert "line 1 column 2" in diagnostic.message
    assert _FILE in str(diagnostic.remediation)
    assert "reported path" not in str(diagnostic.remediation)


def test_wrong_type_path_starts_at_the_file(tmp_path: Path) -> None:
    [diagnostic] = _build(tmp_path, json.dumps({"version": "5.0", "expectations": "none"})).diagnostics

    assert diagnostic.path == (_FILE, "expectations")
    assert "reported path" in str(diagnostic.remediation)


def test_unknown_expectation_kind_is_named_at_the_file(tmp_path: Path) -> None:
    acceptance = json.dumps({"version": "5.0", "expectations": [{"kind": "no_such_kind"}]})
    [diagnostic] = _build(tmp_path, acceptance).diagnostics

    assert diagnostic.path == (_FILE, "expectations", 0)
    assert "unsupported discriminator" in diagnostic.message


def test_expectation_repair_still_applies_under_the_file(tmp_path: Path) -> None:
    range_ = {"kind": "range", "subject": {"kind": "product", "product": "rows"}, "field": "id", "min": 1, "minimum": 1}
    diagnostics = _build(tmp_path, json.dumps({"version": "5.0", "expectations": [range_]})).diagnostics

    assert all(item.path[:2] == (_FILE, "expectations") for item in diagnostics)
    assert any(str(item.remediation).startswith("Write only one of min and minimum.") for item in diagnostics)


def test_valid_file_is_not_rejected_for_the_file(tmp_path: Path) -> None:
    write_project(tmp_path, _XML)
    (tmp_path / PROJECT_ACCEPTANCE_PATH).write_text(
        json.dumps({"version": "5.0", "expectations": [_COUNT]}), encoding="utf-8"
    )

    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert not isinstance(result, RejectedBuild), result


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
@pytest.mark.parametrize("acceptance", ["{oops", json.dumps({"version": "5.0", "expectations": "none"})])
async def test_cli_and_mcp_return_the_same_diagnostic(anyio_backend: str, tmp_path: Path, acceptance: str) -> None:
    fastmcp_client = pytest.importorskip("fastmcp.client")
    from datamimic_ce.interfaces.mcp.server import create_server

    write_project(tmp_path, _XML)
    (tmp_path / PROJECT_ACCEPTANCE_PATH).write_text(acceptance, encoding="utf-8")
    cli = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    async with fastmcp_client.Client(create_server()) as client:
        mcp = await client.call_tool("datamimic_build", {"project": str(tmp_path)})

    contract = TypeAdapter(BuildResult)
    assert cli.exit_code == 1, cli.stdout
    assert contract.validate_json(mcp.content[0].text) == contract.validate_json(cli.stdout)
    assert contract.validate_json(cli.stdout).diagnostics[0].path[0] == _FILE
