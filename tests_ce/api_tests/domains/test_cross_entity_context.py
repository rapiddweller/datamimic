"""Cross-entity regression tests for shared demographic contexts."""

from __future__ import annotations

from random import Random

import pytest

from datamimic_ce.domains.common.demographics.profile import (
    DemographicAgeBand,
    DemographicConditionRate,
    DemographicProfile,
    DemographicProfileId,
)
from datamimic_ce.domains.common.demographics.profile_meta import profile_group_refs
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler


@pytest.fixture()
def shared_profile() -> DemographicProfile:
    profile_id = DemographicProfileId(dataset="US", version="v1")
    age_bands = {
        None: (
            DemographicAgeBand(None, 0, 17, 0.20),
            DemographicAgeBand(None, 18, 44, 0.55),
            DemographicAgeBand(None, 45, 90, 0.25),
        )
    }
    condition_rates = {
        "Hypertension": (
            DemographicConditionRate("Hypertension", None, 0, 120, 0.22),
        ),
        "Type 2 Diabetes": (
            DemographicConditionRate("Type 2 Diabetes", None, 0, 120, 0.19),
        ),
    }
    return DemographicProfile(
        profile_id=profile_id,
        age_bands=age_bands,
        condition_rates=condition_rates,
    )


def test_shared_context_consistency(shared_profile: DemographicProfile) -> None:
    refs = profile_group_refs(
        dataset="US",
        version="v1",
        profile_id="urban_adult",
        request_hash="cross-entity",
    )
    sampler = DemographicSampler(shared_profile)
    sampler.apply_profile_groups(refs, "US", "v1")

    rng_person = Random(2024)
    age_person, sex_person = sampler.sample_age_sex(rng_person)
    conds_person = sampler.sample_conditions(age_person, sex_person, rng_person)

    rng_patient = Random(2024)
    age_patient, sex_patient = sampler.sample_age_sex(rng_patient)
    conds_patient = sampler.sample_conditions(age_patient, sex_patient, rng_patient)

    rng_doctor = Random(2024)
    age_doctor, sex_doctor = sampler.sample_age_sex(rng_doctor)

    assert (age_person, sex_person) == (age_patient, sex_patient) == (age_doctor, sex_doctor)
    assert conds_person == conds_patient
    assert sampler.provenance_hash()
