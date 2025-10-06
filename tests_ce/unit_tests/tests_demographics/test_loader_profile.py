"""Loader tests for demographic profiles."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from datamimic_ce.domains.common.demographics.loader import load_demographic_profile

_test_dir = Path(__file__).resolve().parent

@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    fixture_dir = Path(_test_dir/ "data")
    for name in ("age_pyramid.dmgrp.csv", "condition_rates.dmgrp.csv"):
        shutil.copy(fixture_dir / name, tmp_path / name)
    return tmp_path


def test_load_profile_normalizes_and_indexes(profile_dir: Path) -> None:
    profile = load_demographic_profile(profile_dir, "TEST", "v1")
    female_bands = profile.bands_for_sex("F")
    male_bands = profile.bands_for_sex("M")
    assert len(female_bands) == 3
    assert len(male_bands) == 3
    assert pytest.approx(sum(b.weight for b in female_bands), rel=1e-9) == 1.0
    assert pytest.approx(sum(b.weight for b in male_bands), rel=1e-9) == 1.0
    rates = profile.conditions_for("Hypertension")
    assert rates and rates[0].prevalence == pytest.approx(0.3)
