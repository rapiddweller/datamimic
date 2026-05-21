# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor service.

This module provides a service for working with Doctor entities.
"""

from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import (
    ADDRESS_GROUP_SPEC,
    AttributeSpec,
    group,
    specs,
)
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.doctor import Doctor


class DoctorService(BaseDomainService[Doctor]):
    """Service for working with Doctor entities.

    This class provides methods for generating, exporting, and working with
    Doctor entities.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ) -> None:
        super().__init__(
            DoctorGenerator(
                dataset=dataset,
                rng=rng,
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
            ),
            Doctor,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return (
            *specs(
                ("doctor_id", "str", "Unique doctor identifier."),
                ("npi_number", "str", "National provider identifier."),
                ("license_number", "str", "Medical license number."),
                ("given_name", "str", "First (given) name."),
                ("family_name", "str", "Last (family) name."),
                ("full_name", "str", "Full display name."),
                ("gender", "str", "Gender."),
                ("birthdate", "datetime", "Date of birth."),
                ("age", "int", "Age in years."),
                ("specialty", "str", "Medical specialty."),
                ("hospital", "dict", "Affiliated hospital details."),
                ("medical_school", "str", "Medical school attended."),
                ("graduation_year", "int", "Year of graduation."),
                ("years_of_experience", "int", "Years of professional experience."),
                ("certifications", "list", "Professional certifications."),
                ("accepting_new_patients", "bool", "Whether accepting new patients."),
                ("office_hours", "dict", "Office hours by day."),
                ("email", "str", "Email address."),
                ("phone", "str", "Phone number."),
            ),
            group("address", "Structured practice address.", ADDRESS_GROUP_SPEC.children),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["healthcare/medical/specialties_{CC}.csv"], start=Path(__file__))
