from __future__ import annotations

from pathlib import Path

import pytest

import datamimic_ce.domains.locales as locales


@pytest.fixture(autouse=True)
def clear_locale_cache() -> None:
    locales.load_locale.cache_clear()
    yield
    locales.load_locale.cache_clear()


def test_no_locale_json_duplication() -> None:
    locale_dir = Path(locales.__file__).parent
    json_files = [path for path in locale_dir.rglob("*.json") if path.is_file()]
    assert json_files == []


def test_ensure_supported_dataset_empty_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(locales, "SUPPORTED_DATASETS", frozenset())
    monkeypatch.setattr(locales, "SUPPORTED_DATASET_CODES", tuple())
    with pytest.raises(ValueError) as excinfo:
        locales._ensure_supported_dataset("en_US", "US")  # type: ignore[attr-defined]
    assert "Supported dataset codes: <none>" in str(excinfo.value)


def test_strict_mode_missing_dataset_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATAMIMIC_STRICT_DATASET", "1")
    with pytest.raises(FileNotFoundError):
        locales._read_weighted_values(Path("non-existent-file.csv"))  # type: ignore[attr-defined]


def test_load_locale_uses_dataset_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []
    original = locales.dataset_path

    def tracking_dataset_path(*parts: str, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(parts)
        return original(*parts, **kwargs)

    monkeypatch.setattr(locales, "dataset_path", tracking_dataset_path)
    pack = locales.load_locale("en_US", "v1")
    assert calls, "dataset_path should be used to resolve locale resources"
    # Ensure locale generation still returns deterministic structure
    assert pack.person["sexes"] == ["F", "M", "X"]
