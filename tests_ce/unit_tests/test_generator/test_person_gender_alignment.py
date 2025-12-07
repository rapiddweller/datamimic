# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.

from __future__ import annotations

from collections import Counter
from datetime import datetime
from random import Random

import pytest

from datamimic_ce.domains.common.demographics.sampler import DemographicSample
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person

PRIMARY_DATASETS = ("DE", "US", "VN")


def _get_name_pools(generator: PersonGenerator, dataset: str) -> tuple[list[str], list[str]]:
    """Test helper to access the internal male/female name pools.

    WHY: We deliberately couple to the internal structure here because the bug we
    want to prevent is exactly “wrong pool used for a given gender”. If the
    dataset structure changes, this helper is the single place to adapt.
    """
    female = getattr(generator.given_name_generator, "_dataset_female", None)
    male = getattr(generator.given_name_generator, "_dataset_male", None)

    assert female is not None, f"{dataset} must define _dataset_female for this test"
    assert male is not None, f"{dataset} must define _dataset_male for this test"

    # Current structure: (names, weights, ...)
    return list(female[0]), list(male[0])


@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
def test_person_gender_respects_demographic_labels(dataset: str) -> None:
    generator = PersonGenerator(dataset=dataset, rng=Random(7))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None,
        sex="female",
        conditions=frozenset(),
    )

    female_pool, _ = _get_name_pools(generator, dataset)

    # Sample multiple persons to reduce “lucky” passes.
    for _ in range(5):
        person = Person(generator)

        assert person.gender == "female"
        assert person.given_name in female_pool


@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
def test_person_gender_handles_long_male_codes(dataset: str) -> None:
    generator = PersonGenerator(dataset=dataset, rng=Random(9))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None,
        sex="male",
        conditions=frozenset(),
    )

    _, male_pool = _get_name_pools(generator, dataset)

    for _ in range(5):
        person = Person(generator)

        assert person.gender == "male"
        assert person.given_name in male_pool


@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
def test_person_gender_handles_other_bucket(dataset: str) -> None:
    generator = PersonGenerator(dataset=dataset, rng=Random(21))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None,
        sex="other",
        conditions=frozenset(),
    )

    female_pool, male_pool = _get_name_pools(generator, dataset)
    other_pool = male_pool + female_pool

    for _ in range(5):
        person = Person(generator)

        assert person.gender == "other"
        assert person.given_name in other_pool


class _SentinelGenerator:
    def __init__(self, value: str):
        self.value = value
        self.calls = 0

    def generate(self) -> str:
        self.calls += 1
        return self.value


class _SentinelGenderGenerator(_SentinelGenerator):
    def generate(self) -> str:  # type: ignore[override]
        self.calls += 1
        return self.value


class _SentinelGivenNameGenerator:
    def __init__(self, value: str):
        self.value = value
        self.calls: list[str] = []

    def generate_with_gender(self, gender: str) -> str:
        self.calls.append(gender)
        return self.value


class _SentinelBirthdateGenerator:
    def __init__(self, convert_age: int):
        self.convert_age = convert_age
        self.convert_calls = 0
        self.generate_calls = 0

    def generate(self) -> datetime:
        self.generate_calls += 1
        return datetime(1990, 1, 1)

    def convert_birthdate_to_age(self, birth_date: datetime) -> int:  # noqa: ARG002
        self.convert_calls += 1
        return self.convert_age


class _SentinelAddressGenerator:
    def __init__(self):
        self.dataset = "DE"
        self.rng = Random(11)
        self.street_name_generator = _SentinelGenerator("Teststreet")
        self.city_generator = _StaticCityGenerator()
        self.country_generator = _StaticCountryGenerator()
        self.phone_number_generator = _SentinelGenerator("+49-30-123456")
        self.company_name_generator = _SentinelGenerator("Example GmbH")


class _StaticCityGenerator:
    def get_random_city(self) -> dict[str, str]:
        return {
            "name": "Berlin",
            "area_code": "030",
            "state": "BE",
            "postal_code": "10115",
        }


class _StaticCountryGenerator:
    def get_country_by_iso_code(self, code: str) -> tuple[str, str, str, str, str]:  # noqa: ARG002
        return ("", "", "", "", "Germany")


class _SentinelPersonGenerator:
    def __init__(self, sample: DemographicSample):
        self.reserve_demographic_sample = lambda: sample
        self.gender_generator = _SentinelGenderGenerator("male")
        self.given_name_generator = _SentinelGivenNameGenerator("Max")
        self.family_name_generator = _SentinelGenerator("Mustermann")
        self.email_generator = self
        self.phone_generator = _SentinelGenerator("+49-30-123456")
        self.address_generator = _SentinelAddressGenerator()
        self.birthdate_generator = _SentinelBirthdateGenerator(
            convert_age=sample.age or 30
        )
        self.generated_birthdates: list[int] = []

    def generate_birthdate_for_age(self, age: int) -> datetime:
        self.generated_birthdates.append(age)
        return datetime(2020 - age, 1, 1)

    def generate_with_name(self, given_name: str, family_name: str) -> str:
        return f"{given_name.lower()}.{family_name.lower()}@example.com"


@pytest.mark.parametrize(
    "sex, expected",
    [
        ("female", "female"),
        ("F", "female"),
        ("Male", "male"),
        (" m ", "male"),
        ("Other", "other"),
    ],
)
@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
def test_person_gender_normalizes_common_codes(dataset: str, sex: str, expected: str) -> None:
    generator = PersonGenerator(dataset=dataset, rng=Random(33))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None,
        sex=sex,
        conditions=frozenset(),
    )

    person = Person(generator)

    assert person.gender == expected


def test_person_relations_use_demographic_sample_and_cache() -> None:
    sample = DemographicSample(age=32, sex=" FEMALE", conditions=frozenset())
    generator = _SentinelPersonGenerator(sample)

    person = Person(generator)

    # gender and name resolution
    assert person.gender == "female"
    assert person.given_name == "Max"
    assert generator.given_name_generator.calls == ["female"]

    # family name / full name / alias
    assert person.family_name == "Mustermann"
    assert person.full_name == "Max Mustermann"
    assert person.name == "Max Mustermann"

    # contact details
    assert person.email == "max.mustermann@example.com"
    assert person.phone == "+49-30-123456"
    assert person.mobile_phone == "+49-30-123456"

    # address wiring
    assert isinstance(person.address, Address)
    assert person.address.full_address.endswith("Germany")

    # age / birthdate semantics
    assert person.age == 32
    assert generator.generated_birthdates == [32]
    assert generator.birthdate_generator.convert_calls == 1
    assert person.birthdate.year == 2020 - sample.age

# ---------------------------------------------------------------------------
# Distribution / quota tests
# ---------------------------------------------------------------------------

def _sample_gender_distribution(
    dataset: str,
    female_quota: float,
    other_gender_quota: float,
    n: int = 500,
) -> dict[str, float]:
    """Sample N persons and return empirical gender ratios.

    ASSUMPTION: PersonGenerator accepts female_quota / other_quota, and uses them
    to derive the sampling probabilities for demographic.sex.
    """
    generator = PersonGenerator(
        dataset=dataset,
        rng=Random(123),
        female_quota=female_quota,
        other_gender_quota=other_gender_quota,
    )

    genders = [Person(generator).gender for _ in range(n)]
    counts = Counter(genders)

    return {
        "female": counts.get("female", 0) / n,
        "male": counts.get("male", 0) / n,
        "other": counts.get("other", 0) / n,
    }


@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
def test_person_distribution_respects_extreme_quotas(dataset: str) -> None:
    # female_quota=0, other_gender_quota=0 -> all male
    ratios = _sample_gender_distribution(dataset, female_quota=0.0, other_gender_quota=0.0, n=200)
    assert ratios["female"] == 0.0
    assert ratios["other"] == 0.0
    assert ratios["male"] == 1.0

    # female_quota=1, other_gender_quota=0 -> all female
    ratios = _sample_gender_distribution(dataset, female_quota=1.0, other_gender_quota=0.0, n=200)
    assert ratios["female"] == 1.0
    assert ratios["male"] == 0.0
    assert ratios["other"] == 0.0

    # female_quota=0, other_gender_quota=1 -> all "other"
    ratios = _sample_gender_distribution(dataset, female_quota=0.0, other_gender_quota=1.0, n=200)
    assert ratios["other"] == 1.0
    assert ratios["female"] == 0.0
    assert ratios["male"] == 0.0


@pytest.mark.parametrize("dataset", PRIMARY_DATASETS)
@pytest.mark.parametrize(
    "female_quota, other_quota, tolerance",
    [
        # 0.5 / 0.0: classic male/female split
        (0.5, 0.0, 0.15),
        # 0.0 / 0.5: half other, rest male
        (0.0, 0.5, 0.15),
        # 0.5 / 0.1: mixed distribution (female 50%, other 10%, male 40%)
        (0.5, 0.1, 0.15),
        # 0.0 / 0.1: 10% other, rest male
        (0.0, 0.1, 0.15),
    ],
)
def test_person_distribution_matches_mixed_quotas(
    dataset: str,
    female_quota: float,
    other_quota: float,
    tolerance: float,
) -> None:
    n = 1000
    ratios = _sample_gender_distribution(
        dataset=dataset,
        female_quota=female_quota,
        other_gender_quota=other_quota,
        n=n,
    )

    male_quota = max(0.0, 1.0 - female_quota - other_quota)

    # Each bucket should be within ±tolerance of its configured quota.
    assert female_quota - tolerance <= ratios["female"] <= female_quota + tolerance
    assert other_quota - tolerance <= ratios["other"] <= other_quota + tolerance
    assert male_quota - tolerance <= ratios["male"] <= male_quota + tolerance

    total = ratios["female"] + ratios["male"] + ratios["other"]
    # Sanity: probabilities should sum ~1.0
    assert 0.95 <= total <= 1.05


    