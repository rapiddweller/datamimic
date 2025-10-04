from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.domains.utils.dataset_path import repo_root, domain_data_root, dataset_path


def test_repo_root_discovers_pyproject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    (repo / "sub" / "pkg").mkdir(parents=True)
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n")

    start = repo / "sub" / "pkg" / "file.py"
    start.parent.mkdir(parents=True, exist_ok=True)
    start.write_text("# dummy")

    root = repo_root(start)
    assert root == repo


def test_repo_root_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    forced = tmp_path / "forced_root"
    forced.mkdir(parents=True)
    monkeypatch.setenv("DATAMIMIC_ROOT", str(forced))

    root = repo_root(tmp_path / "any" / "path" / "file.py")
    assert root == forced


def test_domain_data_root_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = tmp_path / "custom_data"
    data.mkdir(parents=True)
    monkeypatch.setenv("DATAMIMIC_DOMAIN_DATA", str(data))

    assert domain_data_root().resolve() == data.resolve()


def test_dataset_path_joining(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    start = repo / "mod" / "file.py"
    start.parent.mkdir(parents=True)
    start.write_text("# d")

    p = dataset_path("healthcare", "medical", "x.csv", start=start)
    assert p == repo / "domain_data" / "healthcare" / "medical" / "x.csv"
