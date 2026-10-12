"""Loader tests for demographic profiles."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from datamimic_ce.domains.shared.demographics.loader import load_demographic_profile
from datamimic_ce.domains.shared.demographics.profile import DemographicAgeBand, DemographicConditionRate

_test_dir = Path(__file__).resolve().parent


@pytest.fixture()
def profile_dir(tmp_path: Path) -> Path:
    fixture_dir = Path(_test_dir / "data")
    for name in ("age_pyramid.dmgrp.csv", "condition_rates.dmgrp.csv"):
        shutil.copy(fixture_dir / name, tmp_path / name)
    return tmp_path


def test_load_profile_normalizes_and_indexes(profile_dir: Path) -> None:
    profile = load_demographic_profile(profile_dir, "TEST", "v1")
    female_bands = profile.bands_for_sex("F")
    male_bands = profile.bands_for_sex("M")
    assert all(isinstance(bands, tuple) for bands in profile.age_bands.values())
    assert all(isinstance(band, DemographicAgeBand) for bands in profile.age_bands.values() for band in bands)
    assert len(female_bands) == 3
    assert len(male_bands) == 3
    assert pytest.approx(sum(b.weight for b in female_bands), rel=1e-9) == 1.0
    assert pytest.approx(sum(b.weight for b in male_bands), rel=1e-9) == 1.0
    rates = profile.conditions_for("Hypertension")
    assert rates and rates[0].prevalence == pytest.approx(0.3)
    assert all(isinstance(rates, tuple) for rates in profile.condition_rates.values())
    assert all(
        isinstance(rate, DemographicConditionRate) for rates in profile.condition_rates.values() for rate in rates
    )


def test_load_profile_keeps_open_normalized_keys_and_combined_fallback(profile_dir: Path) -> None:
    (profile_dir / "age_pyramid.dmgrp.csv").write_text(
        "dataset,version,sex,age_min,age_max,weight\n"
        "TEST,v1, x-custom ,20,100,0.6\n"
        "TEST,v1, x-custom ,0,19,0.4\n"
        "TEST,v1,,0,100,1.0\n",
        encoding="utf-8",
    )
    (profile_dir / "condition_rates.dmgrp.csv").write_text(
        "dataset,version,condition,sex,age_min,age_max,prevalence\n"
        "TEST,v1, Custom condition ,,0,100,0.3\n"
        "TEST,v1, Custom condition , x-custom ,20,100,0.2\n"
        "TEST,v1, Custom condition , x-custom ,0,19,0.1\n",
        encoding="utf-8",
    )

    profile = load_demographic_profile(profile_dir, "TEST", "v1")

    assert set(profile.age_bands) == {"X-CUSTOM", None}
    assert set(profile.condition_rates) == {"Custom condition"}
    assert profile.bands_for_sex(" x-custom ") is profile.age_bands["X-CUSTOM"]
    assert profile.age_bands["X-CUSTOM"] == (
        DemographicAgeBand("X-CUSTOM", 0, 19, 0.4),
        DemographicAgeBand("X-CUSTOM", 20, 100, 0.6),
    )
    assert profile.bands_for_sex("unknown") is profile.age_bands[None]
    assert profile.bands_for_sex(None) is profile.age_bands[None]
    assert profile.conditions_for("Custom condition") is profile.condition_rates["Custom condition"]
    assert profile.condition_rates["Custom condition"] == (
        DemographicConditionRate("Custom condition", "X-CUSTOM", 0, 19, 0.1),
        DemographicConditionRate("Custom condition", "X-CUSTOM", 20, 100, 0.2),
        DemographicConditionRate("Custom condition", None, 0, 100, 0.3),
    )
    assert profile.conditions_for("missing") == ()
