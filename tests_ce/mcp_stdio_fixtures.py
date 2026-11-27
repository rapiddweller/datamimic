# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import sys
from pathlib import Path

import pytest

fastmcp_client = pytest.importorskip("fastmcp.client")
transports = pytest.importorskip("fastmcp.client.transports")
Client = fastmcp_client.Client
PythonStdioTransport = transports.PythonStdioTransport

ROOT = Path(__file__).parents[1]

FIXTURES = ROOT / "tests_ce/unit_tests/test_authoring/project_run"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def stdio_client(cwd: Path) -> object:
    return Client(
        PythonStdioTransport(
            script_path=ROOT / "datamimic_ce/interfaces/mcp/cli.py",
            args=["--transport", "stdio"],
            python_cmd=sys.executable,
            cwd=str(cwd),
            env={"PYTHONPATH": str(ROOT)},
        )
    )
