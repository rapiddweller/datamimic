# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import json
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH

_READBACK = (
    '<setup>\n    <generate name="back" source="shop" selector="SELECT id FROM t" '
    'distribution="ordered" target=""/>\n</setup>\n'
)


def _project(tmp_path: Path, entry: str, step: str = _READBACK) -> Path:
    (tmp_path / "delivery").mkdir()
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "datamimic.xml").write_text(entry, encoding="utf-8")
    (tmp_path / "delivery" / "92_readback.xml").write_text(step, encoding="utf-8")
    (tmp_path / "acceptance" / "build.json").write_text(
        json.dumps({"version": "5.0", "environment_bindings": [{"environment": "shop", "family": "database"}]}),
        encoding="utf-8",
    )
    return tmp_path


def _codes(project: Path) -> list[tuple[str, tuple[object, ...]]]:
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    return [(item.rule or item.code, item.path) for item in result.diagnostics]


_STEP = (
    '<setup{seed}>\n    <generate name="g" count="2"><key name="x" type="int" min="1" max="9"/></generate>\n</setup>\n'
)
