# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app

ROOT = Path(__file__).resolve().parents[1]


def _projects(path: Path) -> list[tuple[str, dict]]:
    """Each documented project: an ``xml`` entry block followed by its ``json`` acceptance block."""
    text = path.read_text()
    entries = re.findall(r"```xml\n(.*?)```", text, re.DOTALL)
    acceptances = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.DOTALL)]
    assert len(entries) == len(acceptances)
    return list(zip(entries, acceptances, strict=True))


def _build(project: tuple[str, dict], workspace: Path) -> dict:
    entry, acceptance = project
    (workspace / "datamimic.xml").write_text(entry, encoding="utf-8")
    (workspace / "acceptance").mkdir()
    (workspace / "acceptance" / "build.json").write_text(json.dumps(acceptance), encoding="utf-8")
    result = CliRunner().invoke(app, ["authoring", "build", str(workspace)])
    payload = json.loads(result.stdout)
    assert result.exit_code == (0 if payload["outcome"] == "ready" else 1), result.stdout
    return payload
