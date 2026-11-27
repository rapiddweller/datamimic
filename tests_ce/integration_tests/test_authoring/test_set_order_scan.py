# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The S17 replay negatives need a full Build under each hash seed."""

import json
import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BuildResult, ReadyBuild, RejectedBuild
from datamimic_ce.authoring.domain.script_semantics import ReplayCause


_S17 = Path(__file__).resolve().parents[2] / "scenarios" / "s17_set_hash_order"

_SET_ORDER_NEGATIVES = ("set_order", "two_element_set", "sorted_key_tie", "dict_view_difference", "variable_set")


def _build_negative(name: str, tmp_path: Path) -> BuildResult:
    project = tmp_path / name
    shutil.copytree(_S17, project, ignore=shutil.ignore_patterns("scenario.json"))
    # scenario.json holds the one patch that makes each negative.
    (patch,) = (
        item["patch"] for item in json.loads((_S17 / "scenario.json").read_text())["negatives"] if item["name"] == name
    )
    entry = project / patch["file"]
    text = entry.read_text(encoding="utf-8")
    assert text.count(patch["old"]) == 1, f"the {name} patch must match exactly once"
    entry.write_text(text.replace(patch["old"], patch["new"]), encoding="utf-8")
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


@pytest.mark.integration
@pytest.mark.parametrize("name", _SET_ORDER_NEGATIVES)
def test_the_replay_under_other_hash_seeds_rejects_each_s17_negative_and_names_a_cause(
    name: str, tmp_path: Path
) -> None:
    built = _build_negative(name, tmp_path)
    assert isinstance(built, RejectedBuild)
    assert built.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert ReplayCause.SET_ORDER.failure_message() in [item.message for item in built.diagnostics]


@pytest.mark.integration
@pytest.mark.parametrize("name", _SET_ORDER_NEGATIVES)
def test_mutant_replays_under_the_first_hash_seed_accept_each_s17_negative(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The negative control: with the first run's hash seed in every replay, nothing tells the runs apart, so
    each rejection above comes from the hash seed change and not from acceptance."""
    from datamimic_ce.authoring.application import build

    monkeypatch.setattr(build, "_REPLAY_HASH_SEEDS", (build._FIRST_RUN_HASH_SEED,) * len(build._REPLAY_HASH_SEEDS))
    assert isinstance(_build_negative(name, tmp_path), ReadyBuild)
