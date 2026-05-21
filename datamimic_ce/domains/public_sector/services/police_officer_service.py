# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer service.

This module provides a service for working with PoliceOfficer entities.
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
from datamimic_ce.domains.public_sector.generators.police_officer_generator import PoliceOfficerGenerator
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer


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
    ):
        super().__init__(
            PoliceOfficerGenerator(
                dataset=dataset,
                rng=rng,
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
            ),
            PoliceOfficer,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return (
            *specs(
                ("officer_id", "str", "Unique officer identifier."),
                ("badge_number", "str", "Badge number."),
                ("given_name", "str", "First (given) name."),
                ("family_name", "str", "Last (family) name."),
                ("full_name", "str", "Full display name."),
                ("gender", "str", "Gender."),
                ("birthdate", "str", "Date of birth."),
                ("age", "int", "Age in years."),
                ("rank", "str", "Officer rank."),
                ("department", "str", "Department."),
                ("unit", "str", "Assigned unit."),
                ("hire_date", "str", "Date of hire."),
                ("years_of_service", "int", "Years of service."),
                ("certifications", "list", "Professional certifications."),
                ("languages", "list", "Languages spoken."),
                ("shift", "str", "Assigned shift."),
                ("email", "str", "Email address."),
                ("phone", "str", "Phone number."),
            ),
            group("address", "Structured officer address.", ADDRESS_GROUP_SPEC.children),
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        """Return ISO dataset codes supported by core required datasets.

        WHY: Keep dataset discovery consistent and DRY across services by
        intersecting required file sets under `domain_data`.
        """
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "public_sector/police/ranks_{CC}.csv",
            "public_sector/police/departments_{CC}.csv",
            "public_sector/police/languages_{CC}.csv",
            "public_sector/police/certifications_{CC}.csv",
            "public_sector/police/shifts_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
