# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from tests_ce.mcp_stdio_fixtures import FIXTURES, stdio_client

pytest_plugins = ("tests_ce.mcp_stdio_fixtures",)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "code,timeout,outcome,truncated",
    [
        ('print("x" * 100000)', 30, "completed", True),
        ("import time; time.sleep(30)", 3, "timeout", False),
        ('raise RuntimeError("test failure")', 30, "failed", False),
    ],
)
async def test_unverified_receipt_after_persistent_write(
    anyio_backend: str, tmp_path: Path, code: str, timeout: int, outcome: str, truncated: bool
) -> None:
    project = tmp_path / "sql_update"
    shutil.copytree(FIXTURES / "sql_update", project)
    entry = project / "datamimic.xml"
    entry.write_text(
        entry.read_text(encoding="utf-8").replace("</setup>", f'<execute type="python">{code}</execute></setup>'),
        encoding="utf-8",
    )
    (project / "db").mkdir()
    with sqlite3.connect(project / "db" / "bank.sqlite") as connection:
        connection.execute("CREATE TABLE bookings (id INTEGER PRIMARY KEY, amount_cents INTEGER)")
        connection.execute("INSERT INTO bookings VALUES (101, -1250)")
    async with stdio_client(tmp_path) as client:
        result = json.loads(
            (
                await client.call_tool(
                    "datamimic_run_project_unverified",
                    {
                        "project": str(project),
                        "confirm_unverified": True,
                        "allow_side_effects": True,
                        "timeout_seconds": timeout,
                    },
                )
            )
            .content[0]
            .text
        )
    assert result["outcome"] == outcome
    assert result["verification"] == "not_verified"
    assert result["details_truncated"] is truncated
    if outcome == "completed":
        assert "partially persisted" not in result["message"]
    else:
        assert "Effects may have partially persisted." in result["message"]
        assert "Inspect the target state independently before retrying." in result["message"]
    with sqlite3.connect(project / "db" / "bank.sqlite") as connection:
        assert connection.execute("SELECT amount_cents FROM bookings WHERE id = 101").fetchone()[0] == -1500
