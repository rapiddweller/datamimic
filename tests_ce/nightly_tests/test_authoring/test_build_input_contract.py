# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import ReadyBuild
from tests_ce.authoring_project import build_project
from tests_ce.build_input_fixtures import _GATES, _entry


@pytest.mark.parametrize("offset", ["", "Z", "+02:00"])
def test_valid_time_series_retains_series_times_window_count(tmp_path: Path, offset: str) -> None:
    entry = _entry(
        f'count="2" start="2026-01-01T00:00:00{offset}" end="2026-01-01T04:00:00{offset}" interval="PT1H"',
        '<key name="v" script="ts.now.isoformat()"/>',
    )
    result = build_project(tmp_path, entry, verification=_GATES)
    assert isinstance(result, ReadyBuild), result
    assert result.evidence[0].count == 8
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED
