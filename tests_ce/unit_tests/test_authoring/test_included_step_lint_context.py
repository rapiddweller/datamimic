# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""An included step is linted in the context of its entry: clients (#493) and the run seed (#472)."""

from pathlib import Path

import pytest

from tests_ce.included_step_fixtures import _STEP, _codes, _project


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


def test_dm320_does_not_fire_for_the_entry_seed(tmp_path: Path) -> None:
    entry = _STEP.format(seed=' rngSeed="1"')
    project = _project(tmp_path, entry)
    (project / "delivery" / "92_readback.xml").unlink()
    assert "DM320" not in [code for code, _ in _codes(project)]
