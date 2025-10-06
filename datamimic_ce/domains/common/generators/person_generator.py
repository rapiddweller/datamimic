# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from __future__ import annotations

from datetime import datetime
from pathlib import Path
from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSample, DemographicSampler
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.academic_title_generator import AcademicTitleGenerator
from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.gender_generator import GenderGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class PersonGenerator(BaseDomainGenerator):
    """Generator for person-related attributes.

    Provides methods to generate person-related attributes such as
    first name, last name, email address, phone number, and address.
    """

    def __init__(
        self,
        dataset: str | None = None,
        min_age: int = 18,
        max_age: int = 65,
        female_quota: float = 0.5,
        other_gender_quota: float = 0.0,
        noble_quota: float = 0.001,
        academic_title_quota: float = 0.5,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ):
        self._dataset = dataset or "US"
        self._rng: Random = rng or Random()
        self._demographic_sampler = demographic_sampler
        # Normalize demographic overrides once to keep SPOT and reuse downstream.
        resolved_config = (demographic_config or DemographicConfig()).with_defaults(
            default_age_min=min_age,
            default_age_max=max_age,
        )
        if (
            resolved_config.age_min is not None
            and resolved_config.age_max is not None
            and resolved_config.age_min > resolved_config.age_max
        ):
            raise ValueError("age_min cannot be greater than age_max")
        # Fan out deterministic RNG copies so rngSeed descriptors yield reproducible composite attributes.
        self._gender_generator = GenderGenerator(
            female_quota=female_quota,
            other_gender_quota=other_gender_quota,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._given_name_generator = GivenNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._family_name_generator = FamilyNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._email_generator = EmailAddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._demographic_config = resolved_config
        self._birth_min = self._demographic_config.age_min if self._demographic_config.age_min is not None else min_age
        self._birth_max = self._demographic_config.age_max if self._demographic_config.age_max is not None else max_age
        # Clamp birthdate sampling to caller-provided bounds without scattering defaults.
        self._birthdate_generator = BirthdateGenerator(
            min_age=self._birth_min,
            max_age=self._birth_max,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._academic_title_generator = AcademicTitleGenerator(
            dataset=self._dataset,
            quota=academic_title_quota,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._nobility_title_generator = NobilityTitleGenerator(
            dataset=self._dataset,
            noble_quota=noble_quota,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._demographic_rng = self._derive_rng() if demographic_sampler is not None and rng is not None else Random()

    def _derive_rng(self) -> Random:
        # Spawn child RNGs from the base seed so seeded descriptors replay without entangling independent draws.
        return Random(self._rng.randrange(2**63)) if isinstance(self._rng, Random) else Random()

    def reserve_demographic_sample(self) -> DemographicSample:
        if self._demographic_sampler is None:
            return DemographicSample(age=None, sex=None, conditions=frozenset())
        age, sex = self._demographic_sampler.sample_age_sex(self._demographic_rng)
        clamped_age = max(self._birth_min, min(self._birth_max, age))
        conditions = self._demographic_sampler.sample_conditions(clamped_age, sex, self._demographic_rng)
        # Sample once per entity so downstream services share consistent demographics.
        return DemographicSample(age=clamped_age, sex=sex, conditions=conditions)

    def generate_birthdate_for_age(self, age: int) -> datetime:
        # Dedicated generator keeps demographic birthdates independent from other literal draws.
        generator = BirthdateGenerator(min_age=age, max_age=age, rng=self._derive_rng())
        return generator.generate()

    @property
    def gender_generator(self) -> GenderGenerator:
        return self._gender_generator

    @property
    def given_name_generator(self) -> GivenNameGenerator:
        return self._given_name_generator

    @property
    def family_name_generator(self) -> FamilyNameGenerator:
        return self._family_name_generator

    @property
    def email_generator(self) -> EmailAddressGenerator:
        return self._email_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_generator(self) -> PhoneNumberGenerator:
        return self._phone_generator

    @property
    def birthdate_generator(self) -> BirthdateGenerator:
        return self._birthdate_generator

    @property
    def academic_title_generator(self) -> AcademicTitleGenerator:
        return self._academic_title_generator

    @property
    def nobility_title_generator(self) -> NobilityTitleGenerator:
        return self._nobility_title_generator

    @property
    def demographic_config(self) -> DemographicConfig:
        """Return the resolved demographic configuration."""

        return self._demographic_config

    def get_salutation_data(self, gender: str) -> str:
        """Get salutation data from CSV file.

        Returns:
            A dictionary containing salutation data.
        """

        salutation_file_path = dataset_path("common", "person", f"salutation_{self._dataset}.csv", start=Path(__file__))
        header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(salutation_file_path, delimiter=",")

        return data[0][header_dict[gender]] if gender in header_dict else ""
