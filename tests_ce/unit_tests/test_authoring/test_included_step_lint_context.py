# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""An included step is linted in the context of its entry: clients (#493) and the run seed (#472)."""

from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
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


@pytest.mark.parametrize(
    ("memstore_id", "dm409"),
    [("x", True), ("mem", False)],
    ids=["memstore_in_step_reuses_client_id", "distinct_ids"],
)
def test_dm409_sees_a_memstore_declared_in_an_included_step(tmp_path: Path, memstore_id: str, dm409: bool) -> None:
    """#712: the client is in the entry, the memstore in an included step; the collision must still be found."""
    entry = (
        '<setup rngSeed="1">\n    <database id="x" dbms="sqlite" database="shop"/>\n'
        '    <include uri="delivery/92_readback.xml"/>\n</setup>\n'
    )
    step = f'<setup>\n    <memstore id="{memstore_id}"/>\n</setup>\n'
    project = _project(tmp_path, entry, step)
    workspace = AuthoringWorkspaceContext(project, PurePosixPath("datamimic.xml"))
    # The entry alone: Build also lints the step, which already saw the client; plain lint of the entry did not.
    entry_lint = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(entry)
    assert ("DM409" in [item.rule for item in entry_lint.diagnostics]) is dm409, entry_lint.diagnostics
    assert ("DM409" in [code for code, _ in _codes(project)]) is dm409


def test_dm320_does_not_fire_for_the_entry_seed(tmp_path: Path) -> None:
    entry = _STEP.format(seed=' rngSeed="1"')
    project = _project(tmp_path, entry)
    (project / "delivery" / "92_readback.xml").unlink()
    assert "DM320" not in [code for code, _ in _codes(project)]
