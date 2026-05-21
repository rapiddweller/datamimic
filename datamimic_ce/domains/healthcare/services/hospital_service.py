# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital service.

This module provides the HospitalService class for generating and managing hospital data.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital

HOSPITAL_SCHEMA = EntitySchema(
    "Hospital",
    (
        field("hospital_id", str, "Unique hospital identifier."),
        field("name", str, "Hospital name."),
        field("type", str, "Hospital type."),
        field("departments", list, "Departments offered."),
        field("services", list, "Services offered."),
        field("bed_count", int, "Number of beds."),
        field("staff_count", int, "Number of staff."),
        field("founding_year", int, "Year founded."),
        field("accreditation", list, "Accreditations held."),
        field("emergency_services", bool, "Whether emergency services are offered."),
        field("teaching_status", bool, "Whether it is a teaching hospital."),
        field("website", str, "Website URL."),
        field("phone", str, "Phone number."),
        field("email", str, "Email address."),
    ),
)


class HospitalService(BaseDomainService[Hospital]):
    """Service for generating and managing hospital data.

    This class provides methods for generating hospital data, exporting it to various formats,
    and retrieving hospitals with specific characteristics.
    """

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(HospitalGenerator(dataset=dataset, rng=rng), Hospital)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return HOSPITAL_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "healthcare/hospital/hospital_types_{CC}.csv",
            "healthcare/hospital/name_patterns_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
