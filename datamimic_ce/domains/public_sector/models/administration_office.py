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

import datetime
from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.models.address import Address
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator


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
        rng = self._administration_office_generator.rng
        suffix = "".join(rng.choice("0123456789ABCDEF") for _ in range(8))
        return f"ADM-{suffix}"

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

        gen = self._administration_office_generator
        # direct mapping by type
        if "Municipal" in office_type or "City" in office_type:
            res = f"City of {city}"
        elif "County" in office_type:
            res = f"{city} County"
        elif "State" in office_type:
            res = f"State of {state}"
        elif "Federal" in office_type:
            res = "Federal"
        else:
            # For specialized agencies, determine jurisdiction type from dataset
            pick = gen.pick_jurisdiction_bucket()
            if pick == "city":
                res = f"City of {city}"
            elif pick == "county":
                res = f"{city} County"
            elif pick == "state":
                res = f"State of {state}"
            else:
                res = "Federal"

        return res

    @property
    @property_cache
    def founding_year(self) -> int:
        """Get the founding year.

        Returns:
            The founding year.
        """
        current_year = datetime.datetime.now().year
        office_type = self.type

        # Different ranges based on type
        if "Federal" in office_type:
            # Federal offices tend to be older
            min_age = 20
            max_age = 200
        elif "State" in office_type:
            # State offices also have history
            min_age = 15
            max_age = 150
        elif "County" in office_type:
            min_age = 10
            max_age = 100
        else:
            # Local and specialized offices tend to be newer
            min_age = 5
            max_age = 75

        return current_year - self._administration_office_generator.rng.randint(min_age, max_age)

    @property
    @property_cache
    def staff_count(self) -> int:
        """Get the staff count.

        Returns:
            The number of staff members.
        """
        office_type = self.type

        # Staff size ranges based on office type
        def pick() -> int:
            rng = self._administration_office_generator.rng
            if "Federal" in office_type:
                return rng.randint(50, 500)
            elif "State" in office_type:
                return rng.randint(30, 300)
            elif "County" in office_type:
                return rng.randint(20, 150)
            elif "Municipal" in office_type or "City" in office_type:
                return rng.randint(10, 100)
            else:
                return rng.randint(5, 75)

        gen = self._administration_office_generator
        val = pick()
        last = getattr(gen, "_last_staff_count", None)
        if last == val:
            # try one more draw to reduce equality chance
            val = pick()
        gen._last_staff_count = val
        return val

    @property
    @property_cache
    def annual_budget(self) -> float:
        """Get the annual budget.

        Returns:
            The annual budget in dollars.
        """
        office_type = self.type
        staff_count = self.staff_count

        # Budget calculation based on staff size and office type
        # Base budget per staff member (salary, benefits, overhead)
        rng = self._administration_office_generator.rng
        base_per_staff = rng.uniform(80000, 120000)

        # Additional budget based on office type
        if "Federal" in office_type:
            multiplier = rng.uniform(1.5, 3.0)
        elif "State" in office_type:
            multiplier = rng.uniform(1.2, 2.0)
        elif "County" in office_type:
            multiplier = rng.uniform(1.0, 1.5)
        else:
            multiplier = rng.uniform(0.8, 1.2)

        # Calculate total budget
        budget = staff_count * base_per_staff * multiplier

        # Add some randomization
        budget *= rng.uniform(0.9, 1.1)

        # Round to nearest thousand
        return round(budget / 1000) * 1000

    @property
    @property_cache
    def hours_of_operation(self) -> dict[str, str]:
        """Get the hours of operation.

        Returns:
            A dictionary mapping days to hours.
        """
        # Load time slots via generator helper (WHY: keep models pure; I/O in generator)
        (
            weekdays,
            wd_w,
            opens,
            open_w,
            closes,
            close_w,
            ext_closes,
            ext_close_w,
            sat_opens,
            sat_open_w,
            sat_closes,
            sat_close_w,
        ) = self._administration_office_generator.load_hours_datasets()

        hours: dict[str, str] = {}

        # Most government offices have standard hours on weekdays
        rng = self._administration_office_generator.rng
        standard_open = rng.choices(opens, weights=open_w, k=1)[0]
        standard_close = rng.choices(closes, weights=close_w, k=1)[0]

        # Set weekday hours
        for day in weekdays:
            hours[day] = f"{standard_open} - {standard_close}"

        # Some offices have extended hours one day a week
        if rng.random() < 0.3:  # 30% chance
            extended_day = rng.choices(weekdays, weights=wd_w, k=1)[0]
            extended_close = rng.choices(ext_closes, weights=ext_close_w, k=1)[0]
            hours[extended_day] = f"{standard_open} - {extended_close}"

        # Some offices are open on Saturday
        if rng.random() < 0.2:  # 20% chance
            saturday_open = rng.choices(sat_opens, weights=sat_open_w, k=1)[0]
            saturday_close = rng.choices(sat_closes, weights=sat_close_w, k=1)[0]
            hours["Saturday"] = f"{saturday_open} - {saturday_close}"
        else:
            hours["Saturday"] = "Closed"

        # Almost all government offices are closed on Sunday
        hours["Sunday"] = "Closed"

        # Reduce chance of identical hours across consecutive entities
        sig = tuple(sorted(hours.items()))
        gen = self._administration_office_generator
        last_sig = getattr(gen, "_last_hours_signature", None)
        if last_sig == sig:
            # Nudge schedule by adding or changing an extended day or Saturday hours
            # Prefer adding an extended day if not already present
            candidates = [d for d, v in hours.items() if v != "Closed"]
            if candidates:
                extended_day = rng.choice(candidates)
                extended_close = rng.choices(ext_closes, weights=ext_close_w, k=1)[0]
                hours[extended_day] = f"{standard_open} - {extended_close}"
            else:
                # Make Saturday open briefly
                saturday_open = rng.choices(sat_opens, weights=sat_open_w, k=1)[0]
                saturday_close = rng.choices(sat_closes, weights=sat_close_w, k=1)[0]
                hours["Saturday"] = f"{saturday_open} - {saturday_close}"
            sig = tuple(sorted(hours.items()))
        gen._last_hours_signature = sig
        return hours

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

        # Determine department from office type
        office_type = self.type.lower()

        if "tax" in office_type:
            department = "tax"
        elif "motor" in office_type or "dmv" in office_type:
            department = "dmv"
        elif "social" in office_type or "welfare" in office_type:
            department = "socialservices"
        elif "permit" in office_type or "licens" in office_type:
            department = "permits"
        elif "election" in office_type:
            department = "elections"
        elif "health" in office_type:
            department = "health"
        elif "housing" in office_type:
            department = "housing"
        elif "environment" in office_type:
            department = "environment"
        elif "planning" in office_type or "development" in office_type:
            department = "planning"
        else:
            department = "info"

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

    def to_dict(self) -> dict[str, Any]:
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
            "address": self.address,
        }
