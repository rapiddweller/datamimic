from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.domains.domain_core.datasets.path import dataset_path, domain_data_root, repo_root
from datamimic_ce.errors import ErrorCode, InvalidDatasetError


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


def _data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "data"
    (root / "common").mkdir(parents=True)
    (root / "common" / "thing_US.csv").write_text("x\n", encoding="utf-8")
    (root / "common" / "other_DE.csv").write_text("x\n", encoding="utf-8")
    monkeypatch.setenv("DATAMIMIC_DOMAIN_DATA", str(root))
    return root


def test_unknown_dataset_is_a_typed_user_error_not_a_us_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _data_root(tmp_path, monkeypatch)

    with pytest.raises(InvalidDatasetError) as raised:
        dataset_path("common", "thing_ZZ.csv")

    assert raised.value.error_code == ErrorCode.INVALID_DATASET
    assert raised.value.dataset == "ZZ"
    assert "Dataset 'ZZ' is not supported" in str(raised.value)


def test_shipped_dataset_without_this_file_keeps_the_us_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _data_root(tmp_path, monkeypatch)

    assert dataset_path("common", "thing_DE.csv") == root / "common" / "thing_US.csv"


def test_city_service_refuses_an_unknown_dataset() -> None:
    from datamimic_ce.domains.shared.services.city_service import CityService

    with pytest.raises(InvalidDatasetError, match="Dataset 'ZZ' is not supported"):
        _ = CityService(dataset="ZZ").generate().name
