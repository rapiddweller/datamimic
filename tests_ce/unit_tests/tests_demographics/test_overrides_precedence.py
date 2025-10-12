"""Tests ensuring demographic overrides trump sampler priors."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from random import Random

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datamimic_ce.domains.common.demographics.loader import load_demographic_profile
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler, DemographicSample
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator

_test_dir = Path(__file__).resolve().parent

def _load_sampler(tmp_path: Path) -> DemographicSampler:
    fixture_dir = Path(_test_dir / "data")
    for name in ("age_pyramid.dmgrp.csv", "condition_rates.dmgrp.csv"):
        shutil.copy(fixture_dir / name, tmp_path / name)
    profile = load_demographic_profile(tmp_path, "TEST", "v1")
    return DemographicSampler(profile)


def test_overrides_adjust_sampled_conditions(tmp_path: Path) -> None:
    sampler = _load_sampler(tmp_path)
    rng = Random(101)
    age, sex = sampler.sample_age_sex(rng)
    sampled_conditions = sampler.sample_conditions(age, sex, rng)
    demo_sample = DemographicSample(age=age, sex=sex, conditions=sampled_conditions)
    overrides = DemographicConfig(
        conditions_include=frozenset({"Hypertension"}),
        conditions_exclude=frozenset({"Asthma"}),
    )
    generator = PatientGenerator(
        dataset="US",
        demographic_config=overrides,
        demographic_sampler=sampler,
        rng=Random(2024),
    )
    conditions = generator.generate_age_appropriate_conditions(age, demo_sample)
    assert "Hypertension" in set(conditions)
    assert all(cond.lower() != "asthma" for cond in conditions)
