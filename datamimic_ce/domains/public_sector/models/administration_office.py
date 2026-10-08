# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office entity model.

This module provides the AdministrationOffice entity model for generating
realistic public administration office data.
"""

from pathlib import Path

from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.shared.models.address import Address


class AdministrationOffice(BaseEntity):
    """Generate administration office data.

    This class generates realistic public administration office data including
    office IDs, names, types, jurisdictions, addresses, contact information,
    staff counts, budgets, services, and departments.

    It uses AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    def __init__(self, administration_office_generator: AdministrationOfficeGenerator):
        super().__init__()
        self._administration_office_generator = administration_office_generator

    @property
    def dataset(self) -> str:
        return self._administration_office_generator.dataset  #  keep dataset lookups aligned with generator config

    # Property getters
    @property
    @property_cache
    def office_id(self) -> str:
        """Get the office ID.

        Returns:
            A unique identifier for the office.
        """
        candidate = self._administration_office_generator.generate_office_id_candidate()
        return self._claim_identifier("office_id", candidate)

    @property
    @property_cache
    def address(self) -> Address:
        """Get the office address.

        Returns:
            The office address.
        """
        return Address(self._administration_office_generator.address_generator)

    @property
    @property_cache
    def name(self) -> str:
        """Get the office name.

        Returns:
            The office name.
        """
        # Get location information for naming
        city = self.address.city
        state = self.address.state

        # Generate office name based on type and jurisdiction
        office_type = self.type
        jurisdiction = self.jurisdiction

        # Delegate name construction to generator (dataset-driven when available)
        return self._administration_office_generator.build_office_name(
            city=city, state=state, office_type=office_type, jurisdiction=jurisdiction
        )

    @property
    @property_cache
    def type(self) -> str:
        """Get the office type.

        Returns:
            The office type.
        """
        #  move dataset I/O and weighted selection into generator helper
        return self._administration_office_generator.pick_office_type()

    @property
    @property_cache
    def jurisdiction(self) -> str:
        """Get the jurisdiction.

        Returns:
            The jurisdiction.
        """
        office_type = self.type
        city = self.address.city
        state = self.address.state
        return self._administration_office_generator.generate_jurisdiction(office_type, city, state)

    @property
    @property_cache
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        current_year = self._administration_office_generator.reference_now.year
        office_type = self.type
        return self._administration_office_generator.generate_founding_year(office_type, current_year)

    @property
    @property_cache
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        return self._administration_office_generator.pick_staff_count(self.type)

    @property
    @property_cache
    def annual_budget(self) -> float:
        """Get the annual budget.

        Returns:
            The annual budget in dollars.
        """
        office_type = self.type
        staff_count = self.staff_count
        return self._administration_office_generator.generate_annual_budget(office_type, staff_count)

    @property
    @property_cache
    def hours_of_operation(self) -> dict[str, str]:
        """Get the hours of operation.

        Returns:
            A dictionary mapping days to hours.
        """
        return self._administration_office_generator.generate_hours_of_operation()

    @property
    @property_cache
    def website(self) -> str:
        """Get the office website.

        Returns:
            The office website URL.
        """
        # Derive from jurisdiction
        jurisdiction = self.jurisdiction.lower()

        # Clean up the jurisdiction for URL
        url_name = jurisdiction.replace("city of ", "")
        url_name = url_name.replace("state of ", "")
        url_name = url_name.replace(" county", "county")
        url_name = url_name.replace(" ", "")
        url_name = "".join(c for c in url_name if c.isalnum())

        # Determine domain extension based on jurisdiction
        domain = ".gov"

        return f"https://www.{url_name}{domain}"

    @property
    @property_cache
    def email(self) -> str:
        """Get the office email address.

        Returns:
            The office email address.
        """
        # Extract domain from website
        website = self.website
        domain = website.replace("https://www.", "")
        office_type = self.type.lower()
        department = self._administration_office_generator.get_email_department(office_type)
        return f"{department}@{domain}"

    @property
    @property_cache
    def phone(self) -> str:
        """Get the office phone number.

        Returns:
            The office phone number.
        """
        return self._administration_office_generator.phone_number_generator.generate()

    @property
    @property_cache
    def services(self) -> list[str]:
        """Get the services offered.

        Returns:
            A list of services.
        """
        return self._administration_office_generator.pick_services(start=Path(__file__))

    @property
    @property_cache
    def departments(self) -> list[str]:
        """Get the departments.

        Returns:
            A list of departments.
        """
        return self._administration_office_generator.pick_departments(start=Path(__file__))

    @property
    @property_cache
    def leadership(self) -> dict[str, str]:
        """Get the office leadership.

        Returns:
            A dictionary mapping leadership positions to names.
        """
        return self._administration_office_generator.build_leadership(start=Path(__file__))

    def to_dict(self) -> dict[str, object]:
        """Convert the administration office entity to a dictionary.

        Returns:
            A dictionary containing all administration office properties.
        """
        return {
            "office_id": self.office_id,
            "name": self.name,
            "type": self.type,
            "jurisdiction": self.jurisdiction,
            "founding_year": self.founding_year,
            "staff_count": self.staff_count,
            "annual_budget": self.annual_budget,
            "hours_of_operation": self.hours_of_operation,
            "website": self.website,
            "email": self.email,
            "phone": self.phone,
            "services": self.services,
            "departments": self.departments,
            "leadership": self.leadership,
            "address": self.address.to_dict(),
        }
