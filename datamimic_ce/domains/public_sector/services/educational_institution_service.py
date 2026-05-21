# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution service.

This module provides a service for working with EducationalInstitution entities.
"""

from datetime import datetime
from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import (
    EntitySchema,
    FieldSpec,
    address_group,
    field,
)
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution

EDUCATIONAL_INSTITUTION_SCHEMA = EntitySchema(
    "EducationalInstitution",
    (
        field("institution_id", str, "Unique institution identifier."),
        field("name", str, "Institution name."),
        field("type", str, "Institution type."),
        field("level", str, "Education level."),
        field("founding_year", int, "Year the institution was founded."),
        field("student_count", int, "Number of students."),
        field("staff_count", int, "Number of staff."),
        field("website", str, "Website URL."),
        field("email", str, "Email address."),
        field("phone", str, "Phone number."),
        field("programs", list, "Programs offered."),
        field("accreditations", list, "Accreditations held."),
        field("facilities", list, "Available facilities."),
        address_group("address", "Structured institution address."),
    ),
)


class EducationalInstitutionService(BaseDomainService[EducationalInstitution]):
    """Service for working with EducationalInstitution entities.

    This class provides methods for generating, exporting, and working with
    EducationalInstitution entities.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ):
        super().__init__(
            EducationalInstitutionGenerator(dataset=dataset, rng=rng, reference_now=reference_now),
            EducationalInstitution,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return EDUCATIONAL_INSTITUTION_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        """Return ISO dataset codes supported by core required datasets.

        We use a minimal set that guarantees generation works. Additional
        files (programs, accreditations, facilities) are available for
        the same codes in this repository.
        """
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "public_sector/education/institution_types_{CC}.csv",
            "public_sector/education/levels_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
