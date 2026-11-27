# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The evaluation runners fail closed without process-group cleanup on every platform."""

import subprocess
from pathlib import Path

import pytest

from benchmarks.authoring_eval import oracle, run_subject


@pytest.mark.parametrize("runner", ["capture", "subject"])
def test_unsupported_process_groups_fail_before_starting_a_child(
    runner: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delattr(oracle.os, "killpg", raising=False)

    def unexpected_start(*args: object, **kwargs: object) -> None:
        pytest.fail("an untrusted process was started without process-group cleanup")

    monkeypatch.setattr(subprocess, "Popen", unexpected_start)
    with pytest.raises(RuntimeError, match="requires POSIX process groups"):
        if runner == "capture":
            oracle._start(tmp_path, "1")
        else:
            run_subject._execute(["unused"], tmp_path, {}, tmp_path / "out", tmp_path / "err")
