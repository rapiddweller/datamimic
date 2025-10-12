"""Runtime coverage for demographic sampler group application."""

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
from datamimic_ce.domains.common.demographics.sampler import (
    DemographicSampler,
    GroupRegistry,
    MaskBoundsError,
    load_group_table,
)
from datamimic_ce.domains.determinism import compute_provenance_hash
from datamimic_ce.domains.utils.dataset_path import dataset_path


@pytest.fixture()
def sample_profile() -> DemographicProfile:
    profile_id = DemographicProfileId(dataset="US", version="v1")
    age_bands = {
        "Female": (
            DemographicAgeBand("Female", 0, 17, 0.30),
            DemographicAgeBand("Female", 18, 44, 0.45),
            DemographicAgeBand("Female", 45, 90, 0.25),
        ),
        "Male": (
            DemographicAgeBand("Male", 0, 17, 0.35),
            DemographicAgeBand("Male", 18, 44, 0.40),
            DemographicAgeBand("Male", 45, 90, 0.25),
        ),
    }
    condition_rates = {
        "Hypertension": (
            DemographicConditionRate("Hypertension", None, 0, 120, 0.25),
        ),
        "Type 2 Diabetes": (
            DemographicConditionRate("Type 2 Diabetes", None, 0, 120, 0.2),
        ),
        "Seasonal Allergy": (
            DemographicConditionRate("Seasonal Allergy", None, 0, 120, 0.1),
        ),
    }
    return DemographicProfile(
        profile_id=profile_id,
        age_bands=age_bands,
        condition_rates=condition_rates,
    )


def test_group_application_deterministic(sample_profile: DemographicProfile) -> None:
    refs = profile_group_refs(
        dataset="US", version="v1", profile_id="urban_adult", request_hash="demo"
    )
    assert refs, "metadata lookup must return group references"

    sampler_a = DemographicSampler(sample_profile)
    sampler_b = DemographicSampler(sample_profile)

    sampler_a.apply_profile_groups(refs, "US", "v1")
    sampler_b.apply_profile_groups(refs, "US", "v1")

    female_a = sampler_a.age_band_weights("Female")
    female_b = sampler_b.age_band_weights("Female")
    assert set(female_a) == set(female_b)
    for key in female_a:
        assert female_a[key] == pytest.approx(female_b[key])

    cond_a = sampler_a.condition_weights()
    cond_b = sampler_b.condition_weights()
    assert set(cond_a) == set(cond_b)
    for key in cond_a:
        assert cond_a[key] == pytest.approx(cond_b[key])

    sex_a = sampler_a.sex_weights()
    sex_b = sampler_b.sex_weights()
    assert set(sex_a) == set(sex_b)
    for key in sex_a:
        assert sex_a[key] == pytest.approx(sex_b[key])


def test_age_mask_applies_band_filter(
    sample_profile: DemographicProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = dataset_path("groups", "age_band", "age_band_US.csv")
    file_hash = compute_provenance_hash([str(path)])
    original = load_group_table

    def fake_load(dataset: str, version: str, dimension: str, group_id: str):
        if dimension == "age_band":
            mask = {(0, 17): 0.7, (18, 44): 1.4, (45, 90): 0.6}
            return mask, (str(path), file_hash)
        return original(dataset, version, dimension, group_id)

    monkeypatch.setattr(
        "datamimic_ce.domains.common.demographics.sampler.load_group_table",
        fake_load,
    )

    sampler = DemographicSampler(sample_profile)
    sampler.apply_profile_groups({"age_group_ref": "age_18_44"}, "US", "v1")

    female_weights = sampler.age_band_weights("Female")
    assert female_weights[(18, 44)] > female_weights[(0, 17)]
    assert sampler.group_mask("age_band") == {
        (0, 17): 0.7,
        (18, 44): 1.4,
        (45, 90): 0.6,
    }
    descriptor = sampler.provenance_descriptor()
    assert descriptor[str(path)] == file_hash



def test_condition_mask_scales_weights(
    sample_profile: DemographicProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = dataset_path(
        "groups",
        "condition_prevalence_tier",
        "condition_prevalence_tier_US.csv",
    )
    file_hash = compute_provenance_hash([str(path)])
    original = load_group_table

    def fake_load(dataset: str, version: str, dimension: str, group_id: str):
        if dimension == "condition_prevalence_tier":
            mask = {
                "Hypertension": 1.1,
                "Type 2 Diabetes": 1.05,
                "Seasonal Allergy": 0.95,
            }
            return mask, (str(path), file_hash)
        return original(dataset, version, dimension, group_id)

    monkeypatch.setattr(
        "datamimic_ce.domains.common.demographics.sampler.load_group_table",
        fake_load,
    )

    sampler = DemographicSampler(sample_profile)
    sampler.apply_profile_groups({"condition_group_ref": "cond_high_prevalence"}, "US", "v1")
    weights = sampler.condition_weights()
    assert weights["Hypertension"] > weights["Seasonal Allergy"]
    assert pytest.approx(sum(weights.values()), rel=0, abs=1e-9) == 1.0


def test_additional_group_masks_exposed(sample_profile: DemographicProfile) -> None:
    sampler = DemographicSampler(sample_profile)
    refs = profile_group_refs(
        dataset="US", version="v1", profile_id="urban_adult", request_hash="mask"
    )
    sampler.apply_profile_groups(refs, "US", "v1")

    expected_coverage, provenance = load_group_table("US", "v1", "coverage_line", "coverage_other")
    assert provenance is not None
    assert sampler.group_mask("coverage_line") == expected_coverage


def test_mask_bounds_enforced_strict_mode(
    sample_profile: DemographicProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATAMIMIC_STRICT_DATASET", "1")

    def fake_load(*_: object, **__: object) -> tuple[dict[tuple[int, int], float], tuple[str, str]]:
        return ({(18, 44): 1.0}, ("/tmp/fake.csv", "hash"))

    monkeypatch.setattr(
        "datamimic_ce.domains.common.demographics.sampler.load_group_table",
        fake_load,
    )

    sampler = DemographicSampler(sample_profile)
    with pytest.raises(MaskBoundsError):
        sampler.apply_profile_groups({"age_group_ref": "age_18_44"}, "US", "v1")


def test_mask_bounds_fallback_non_strict(
    sample_profile: DemographicProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DATAMIMIC_STRICT_DATASET", raising=False)

    def fake_load(*_: object, **__: object) -> tuple[dict[tuple[int, int], float], tuple[str, str]]:
        return ({(18, 44): 1.0}, ("/tmp/fake.csv", "hash"))

    monkeypatch.setattr(
        "datamimic_ce.domains.common.demographics.sampler.load_group_table",
        fake_load,
    )

    sampler = DemographicSampler(sample_profile)
    sampler.apply_profile_groups({"age_group_ref": "age_18_44"}, "US", "v1")

    female_weights = sampler.age_band_weights("Female")
    assert set(female_weights.keys()) == {(0, 17), (18, 44), (45, 90)}
    assert sampler.group_mask("age_band") == {}
    assert sampler.provenance_descriptor() == {}


def test_provenance_hash_tracks_group_files(
    sample_profile: DemographicProfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = dataset_path("groups", "age_band", "age_band_US.csv")
    file_hash = compute_provenance_hash([str(path)])
    original = load_group_table

    def fake_load(dataset: str, version: str, dimension: str, group_id: str):
        if dimension == "age_band":
            mask = {(0, 17): 0.7, (18, 44): 1.4, (45, 90): 0.6}
            return mask, (str(path), file_hash)
        return original(dataset, version, dimension, group_id)

    monkeypatch.setattr(
        "datamimic_ce.domains.common.demographics.sampler.load_group_table",
        fake_load,
    )

    sampler = DemographicSampler(sample_profile)
    sampler.apply_profile_groups({"age_group_ref": "age_18_44"}, "US", "v1")

    descriptor = sampler.provenance_descriptor()
    assert descriptor[str(path)] == file_hash
    hash_value = sampler.provenance_hash()
    assert hash_value == compute_provenance_hash([str(path)])


def test_group_registry_cache_hits() -> None:
    GroupRegistry._resolve.cache_clear()
    load_group_table("US", "v1", "gender_category", "gender_majority")
    initial_info = GroupRegistry._resolve.cache_info()
    assert initial_info.currsize >= 1
    for _ in range(5):
        load_group_table("US", "v1", "gender_category", "gender_majority")
    updated_info = GroupRegistry._resolve.cache_info()
    assert updated_info.hits - initial_info.hits >= 4
