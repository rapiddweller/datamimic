# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Only a missing Windows privilege skips symlink security tests."""

from pathlib import Path

import pytest

from tests_ce.symlink_fixtures import _probe_symlinks


def test_symlink_probe_cleans_up_successful_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(Path, "symlink_to", lambda path, target, target_is_directory: calls.append(("create", path)))
    monkeypatch.setattr(Path, "unlink", lambda path: calls.append(("unlink", path)))

    _probe_symlinks(tmp_path)

    assert calls == [
        ("create", tmp_path / "symlink-capability-probe"),
        ("unlink", tmp_path / "symlink-capability-probe"),
    ]


def test_symlink_probe_skips_only_missing_windows_privilege(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    error = OSError("missing privilege")
    error.winerror = 1314

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(Path, "symlink_to", fail)
    with pytest.raises(pytest.skip.Exception, match="symlink privilege"):
        _probe_symlinks(tmp_path)


def test_symlink_probe_does_not_hide_other_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise OSError("unexpected failure")

    monkeypatch.setattr(Path, "symlink_to", fail)
    with pytest.raises(OSError, match="unexpected failure"):
        _probe_symlinks(tmp_path)
