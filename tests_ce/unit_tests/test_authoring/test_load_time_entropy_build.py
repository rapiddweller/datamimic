# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A script that draws while it loads (W008, #359) is caught by Build's deterministic replay gate; a script that
draws inside a function passes it. The models are the replay models of
functional_tests/test_seeded_load_time_entropy, copied into a project."""

import shutil
from pathlib import Path

from tests_ce.authoring_project import build_project

_CORPUS = Path(__file__).resolve().parents[2] / "functional_tests" / "test_seeded_load_time_entropy"
_ROWS = [{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 3}]


def _build(tmp_path: Path, model: str):
    shutil.copytree(_CORPUS / "script" / "replay", tmp_path / "script" / "replay")
    return build_project(
        tmp_path,
        (_CORPUS / model).read_text(encoding="utf-8"),
        version="5.0",
        expectations=_ROWS,
        verification={"deterministic_replay": True},
    )


def test_build_rejects_a_draw_at_load_time_because_the_replay_differs(tmp_path: Path) -> None:
    result = _build(tmp_path, "replay_leaky.xml")
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"


def test_build_accepts_a_draw_inside_a_function(tmp_path: Path) -> None:
    result = _build(tmp_path, "replay_quiet.xml")
    assert result.outcome == "ready", result.diagnostics
    assert result.verification.deterministic_replay.status.value == "passed"
