# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""An included step is linted in the context of its entry: clients (#493) and the run seed (#472)."""

import json
from pathlib import Path

import pytest

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
    return [(item.code, item.path) for item in result.diagnostics]


@pytest.mark.parametrize(
    ("client", "dm211"),
    [
        ('<database id="shop" dbms="sqlite" database="shop"/>', False),
        ('<database id="other" dbms="sqlite" database="shop"/>', True),
        ("", True),
    ],
    ids=["client_declared_in_entry", "other_client_in_entry", "no_client"],
)
def test_dm211_in_an_included_step_sees_the_clients_of_the_entry(tmp_path: Path, client: str, dm211: bool) -> None:
    entry = f'<setup rngSeed="1">\n    {client}\n    <include uri="delivery/92_readback.xml"/>\n</setup>\n'
    codes = _codes(_project(tmp_path, entry))
    assert (("DM211", ("include", "delivery/92_readback.xml")) in [(c, p[:2]) for c, p in codes]) is dm211, codes
