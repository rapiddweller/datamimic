"""Determinism tests for the demographic sampler."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from datamimic_ce.domains.common.demographics.loader import load_demographic_profile
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler

_test_dir = Path(__file__).resolve().parent

@pytest.fixture()
def sampler(tmp_path: Path) -> DemographicSampler:
    fixture_dir = Path(_test_dir / "data")
    for name in ("age_pyramid.dmgrp.csv", "condition_rates.dmgrp.csv"):
        shutil.copy(fixture_dir / name, tmp_path / name)
    profile = load_demographic_profile(tmp_path, "TEST", "v1")
    return DemographicSampler(profile)


def test_age_sex_sampling_is_deterministic(sampler: DemographicSampler) -> None:
    rng_a = Random(123)
    rng_b = Random(123)
    sequence_a = [sampler.sample_age_sex(rng_a) for _ in range(10)]
    sequence_b = [sampler.sample_age_sex(rng_b) for _ in range(10)]
    assert sequence_a == sequence_b


def test_condition_sampling_is_deterministic(sampler: DemographicSampler) -> None:
    rng_a = Random(987)
    rng_b = Random(987)
    draws_a = []
    draws_b = []
    for _ in range(10):
        age_a, sex_a = sampler.sample_age_sex(rng_a)
        draws_a.append(sampler.sample_conditions(age_a, sex_a, rng_a))
        age_b, sex_b = sampler.sample_age_sex(rng_b)
        draws_b.append(sampler.sample_conditions(age_b, sex_b, rng_b))
    assert draws_a == draws_b
