# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor service.

This module provides a service for working with Doctor entities.
"""

from datetime import datetime
from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import (
    EntitySchema,
    FieldSpec,
    address_group,
    field,
)
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.doctor import Doctor

DOCTOR_SCHEMA = EntitySchema(
    "Doctor",
    (
        field("doctor_id", str, "Unique doctor identifier."),
        field("npi_number", str, "National provider identifier."),
        field("license_number", str, "Medical license number."),
        field("given_name", str, "First (given) name."),
        field("family_name", str, "Last (family) name."),
        field("full_name", str, "Full display name."),
        field("gender", str, "Gender."),
        field("birthdate", datetime, "Date of birth."),
        field("age", int, "Age in years."),
        field("specialty", str, "Medical specialty."),
        field("hospital", dict, "Affiliated hospital details."),
        field("medical_school", str, "Medical school attended."),
        field("graduation_year", int, "Year of graduation."),
        field("years_of_experience", int, "Years of professional experience."),
        field("certifications", list, "Professional certifications."),
        field("accepting_new_patients", bool, "Whether accepting new patients."),
        field("office_hours", dict, "Office hours by day."),
        field("email", str, "Email address."),
        field("phone", str, "Phone number."),
        address_group("address", "Structured practice address."),
    ),
)


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
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return DOCTOR_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["healthcare/medical/specialties_{CC}.csv"], start=Path(__file__))
