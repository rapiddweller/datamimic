# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office service.

This module provides a service for working with AdministrationOffice entities.
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
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice

ADMINISTRATION_OFFICE_SCHEMA = EntitySchema(
    "AdministrationOffice",
    (
        field("office_id", str, "Unique office identifier."),
        field("name", str, "Office name."),
        field("type", str, "Office type."),
        field("jurisdiction", str, "Jurisdiction served."),
        field("founding_year", int, "Year the office was founded."),
        field("staff_count", int, "Number of staff."),
        field("annual_budget", float, "Annual budget."),
        field("hours_of_operation", dict, "Operating hours by day."),
        field("website", str, "Website URL."),
        field("email", str, "Email address."),
        field("phone", str, "Phone number."),
        field("services", list, "Services offered."),
        field("departments", list, "Departments within the office."),
        field("leadership", dict, "Leadership roles and names."),
        address_group("address", "Structured office address."),
    ),
)


class AdministrationOfficeService(BaseDomainService[AdministrationOffice]):
    """Service for working with AdministrationOffice entities.

    This class provides methods for generating, exporting, and working with
    AdministrationOffice entities.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
        reference_now: datetime | None = None,
    ):
        super().__init__(
            AdministrationOfficeGenerator(dataset=dataset, rng=rng, reference_now=reference_now),
            AdministrationOffice,
        )

    DATASET_PATTERNS = (
        "public_sector/administration/office_types_{CC}.csv",
        "public_sector/administration/jurisdictions_{CC}.csv",
        "public_sector/administration/name_patterns_{CC}.csv",
        "public_sector/administration/roles_{CC}.csv",
        "public_sector/administration/agencies_{CC}.csv",
        "public_sector/administration/weekdays_{CC}.csv",
        "public_sector/administration/open_times_{CC}.csv",
        "public_sector/administration/close_times_{CC}.csv",
        "public_sector/administration/extended_close_times_{CC}.csv",
        "public_sector/administration/saturday_open_times_{CC}.csv",
        "public_sector/administration/saturday_close_times_{CC}.csv",
    )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return ADMINISTRATION_OFFICE_SCHEMA.fields
