# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.

from __future__ import annotations

from datetime import datetime
from random import Random

import pytest

from datamimic_ce.domains.common.demographics.sampler import DemographicSample
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.common.models.person import Person


def test_person_gender_respects_demographic_labels() -> None:
    generator = PersonGenerator(dataset="DE", rng=Random(7))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None, sex="female", conditions=frozenset()
    )

    person = Person(generator)

    assert person.gender == "female"
    assert person.given_name in generator.given_name_generator._dataset_female[0]


def test_person_gender_handles_long_male_codes() -> None:
    generator = PersonGenerator(dataset="DE", rng=Random(9))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None, sex="male", conditions=frozenset()
    )

    person = Person(generator)

    assert person.gender == "male"
    assert person.given_name in generator.given_name_generator._dataset_male[0]


def test_person_gender_handles_other_bucket() -> None:
    generator = PersonGenerator(dataset="DE", rng=Random(21))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None, sex="other", conditions=frozenset()
    )

    person = Person(generator)

    assert person.gender == "other"
    assert person.given_name in (
        generator.given_name_generator._dataset_male[0]
        + generator.given_name_generator._dataset_female[0]
    )


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
        self.birthdate_generator = _SentinelBirthdateGenerator(convert_age=sample.age or 30)
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
def test_person_gender_normalizes_common_codes(sex: str, expected: str) -> None:
    generator = PersonGenerator(dataset="DE", rng=Random(33))
    generator.reserve_demographic_sample = lambda: DemographicSample(
        age=None, sex=sex, conditions=frozenset()
    )

    person = Person(generator)

    assert person.gender == expected


def test_person_relations_use_demographic_sample_and_cache() -> None:
    sample = DemographicSample(age=32, sex=" FEMALE", conditions=frozenset())
    generator = _SentinelPersonGenerator(sample)

    person = Person(generator)

    assert person.gender == "female"
    assert person.given_name == "Max"
    assert generator.given_name_generator.calls == ["female"]
    assert person.family_name == "Mustermann"
    assert person.full_name == "Max Mustermann"
    assert person.name == "Max Mustermann"
    assert person.email == "max.mustermann@example.com"
    assert person.phone == "+49-30-123456"
    assert person.mobile_phone == "+49-30-123456"
    assert isinstance(person.address, Address)
    assert person.address.full_address.endswith("Germany")
    assert person.age == 32
    assert generator.generated_birthdates == [32]
    assert generator.birthdate_generator.convert_calls == 1
    assert person.birthdate.year == 2020 - sample.age
