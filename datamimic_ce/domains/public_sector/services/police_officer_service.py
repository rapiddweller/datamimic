# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer service.

This module provides a service for working with PoliceOfficer entities.
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
from datamimic_ce.domains.public_sector.generators.police_officer_generator import PoliceOfficerGenerator
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer

POLICE_OFFICER_SCHEMA = EntitySchema(
    "PoliceOfficer",
    (
        field("officer_id", str, "Unique officer identifier."),
        field("badge_number", str, "Badge number."),
        field("given_name", str, "First (given) name."),
        field("family_name", str, "Last (family) name."),
        field("full_name", str, "Full display name."),
        field("gender", str, "Gender."),
        field("birthdate", datetime, "Date of birth."),
        field("age", int, "Age in years."),
        field("rank", str, "Officer rank."),
        field("department", str, "Department."),
        field("unit", str, "Assigned unit."),
        field("hire_date", str, "Date of hire."),
        field("years_of_service", int, "Years of service."),
        field("certifications", list, "Professional certifications."),
        field("languages", list, "Languages spoken."),
        field("shift", str, "Assigned shift."),
        field("email", str, "Email address."),
        field("phone", str, "Phone number."),
        address_group("address", "Structured officer address."),
    ),
)


class PoliceOfficerService(BaseDomainService[PoliceOfficer]):
    """Service for working with PoliceOfficer entities.

    This class provides methods for generating, exporting, and working with
    PoliceOfficer entities.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ):
        super().__init__(
            PoliceOfficerGenerator(
                dataset=dataset,
                rng=rng,
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
                reference_now=reference_now,
            ),
            PoliceOfficer,
        )

    DATASET_PATTERNS = (
        "public_sector/police/ranks_{CC}.csv",
        "public_sector/police/departments_{CC}.csv",
        "public_sector/police/languages_{CC}.csv",
        "public_sector/police/certifications_{CC}.csv",
        "public_sector/police/shifts_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return POLICE_OFFICER_SCHEMA.fields
