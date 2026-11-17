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


_STEP = (
    '<setup{seed}>\n    <generate name="g" count="2"><key name="x" type="int" min="1" max="9"/></generate>\n</setup>\n'
)


@pytest.mark.parametrize(
    ("entry_seed", "step_seed", "fires"),
    [
        (' rngSeed="1"', ' rngSeed="9"', True),
        (' rngSeed="1"', "", False),
        ("", ' rngSeed="9"', True),
    ],
    ids=["step_with_seed", "step_without_seed", "unseeded_entry_step_with_seed"],
)
def test_dm320_warns_when_an_included_step_sets_its_own_rng_seed(
    tmp_path: Path, entry_seed: str, step_seed: str, fires: bool
) -> None:
    entry = f'<setup{entry_seed}>\n    <include uri="delivery/92_readback.xml"/>\n</setup>\n'
    project = _project(tmp_path, entry, _STEP.format(seed=step_seed))
    findings = [(c, p[:2]) for c, p in _codes(project)]
    assert (("DM320", ("include", "delivery/92_readback.xml")) in findings) is fires, findings


def test_dm320_does_not_fire_for_the_entry_seed(tmp_path: Path) -> None:
    entry = _STEP.format(seed=' rngSeed="1"')
    project = _project(tmp_path, entry)
    (project / "delivery" / "92_readback.xml").unlink()
    assert "DM320" not in [code for code, _ in _codes(project)]
