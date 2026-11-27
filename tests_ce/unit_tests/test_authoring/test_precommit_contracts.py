# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import os

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import _child_environment
from datamimic_ce.authoring.domain.requests import BUILD_PROTOCOL, BuildRequestV5


def test_build_protocol_matches_the_acceptance_contract() -> None:
    assert BuildRequestV5().version == BUILD_PROTOCOL == "5.0"


def test_child_environment_adds_project_values_without_touching_this_process(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROJECT_ONLY_VALUE", raising=False)
    assert _child_environment({}, None) is None
    child = _child_environment({"PROJECT_ONLY_VALUE": "1"}, 5)
    assert child is not None and child["PROJECT_ONLY_VALUE"] == "1" and child["PYTHONHASHSEED"] == "5"
    assert "PROJECT_ONLY_VALUE" not in os.environ
