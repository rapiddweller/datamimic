"""Statistical checks for demographic sampling."""

from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from datamimic_ce.domains.common.demographics.loader import load_demographic_profile
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler

_test_dir = Path(__file__).resolve().parent

@pytest.fixture()
def profile_and_sampler(tmp_path: Path):
    fixture_dir = Path(_test_dir / "data")
    for name in ("age_pyramid.dmgrp.csv", "condition_rates.dmgrp.csv"):
        shutil.copy(fixture_dir / name, tmp_path / name)
    profile = load_demographic_profile(tmp_path, "TEST", "v1")
    return profile, DemographicSampler(profile)


def test_age_distribution_matches_profile(profile_and_sampler) -> None:
    profile, sampler = profile_and_sampler
    rng = Random(2024)
    sexes = [sex for sex in profile.sexes() if sex is not None]
    counts = {sex: Counter() for sex in sexes}
    samples = 50000
    for _ in range(samples):
        age, sex = sampler.sample_age_sex(rng)
        bands = profile.bands_for_sex(sex)
        for band in bands:
            if band.contains(age):
                counts[sex][(band.age_min, band.age_max)] += 1
                break
    chi_square = 0.0
    degrees_of_freedom = 0
    expected_per_sex = samples / max(len(sexes), 1)
    for sex in sexes:
        bands = profile.bands_for_sex(sex)
        degrees_of_freedom += max(len(bands) - 1, 0)
        for band in bands:
            expected = expected_per_sex * band.weight
            observed = counts[sex][(band.age_min, band.age_max)]
            chi_square += (observed - expected) ** 2 / expected
    # Critical value for df=4, alpha=0.05 is ~9.488
    assert degrees_of_freedom == 4
    assert chi_square <= 9.488
