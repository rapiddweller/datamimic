"""Ensure no locale JSON datasets sneak into the codebase."""
from __future__ import annotations

from pathlib import Path


def test_no_locale_json_datasets() -> None:
    locale_dir = Path("datamimic_ce/domains/locales")
    assert locale_dir.exists(), "Locale directory missing"
    json_files = list(locale_dir.rglob("*.json"))
    assert not json_files, f"Found unexpected locale JSON datasets: {json_files}"
