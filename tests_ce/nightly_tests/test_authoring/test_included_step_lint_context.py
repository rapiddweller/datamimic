# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest

from tests_ce.included_step_fixtures import _STEP, _codes, _project


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
