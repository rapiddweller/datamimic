"""Guardrail to ensure locale data stays under domain_data (rule 1)."""
from pathlib import Path

import datamimic_ce.domains.locales as locales_module


def test_no_locale_json_duplication() -> None:
    locale_dir = Path(locales_module.__file__).resolve().parent
    json_files = list(locale_dir.glob("**/*.json"))
    assert not json_files
