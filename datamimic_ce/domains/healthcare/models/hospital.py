# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital entity model.

This module provides the Hospital entity model for generating realistic hospital data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.healthcare.data_loaders.hospital_loader import HospitalDataLoader


class Hospital(BaseEntity):
    """Generate hospital data.

    This class generates realistic hospital data including hospital names,
    types, departments, services, staff counts, and contact information.

    It uses AddressEntity for generating address information.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Class-level cache for shared data
    _DATA_CACHE: ClassVar[dict[str, Any]] = {}

    def __init__(
        self,
        class_factory_util: Any,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the Hospital entity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._dataset = dataset
        self._country_code = dataset or "US"

        # Initialize data loader
        self._data_loader = HospitalDataLoader()

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._hospital_id_generator = PropertyCache(self._generate_hospital_id)
        self._name_generator = PropertyCache(self._generate_name)
        self._type_generator = PropertyCache(self._generate_type)
        self._departments_generator = PropertyCache(self._generate_departments)
        self._services_generator = PropertyCache(self._generate_services)
        self._bed_count_generator = PropertyCache(self._generate_bed_count)
        self._staff_count_generator = PropertyCache(self._generate_staff_count)
        self._founding_year_generator = PropertyCache(self._generate_founding_year)
        self._accreditation_generator = PropertyCache(self._generate_accreditation)
        self._emergency_services_generator = PropertyCache(self._generate_emergency_services)
        self._teaching_status_generator = PropertyCache(self._generate_teaching_status)
        self._website_generator = PropertyCache(self._generate_website)
        self._phone_generator = PropertyCache(self._generate_phone)
        self._email_generator = PropertyCache(self._generate_email)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._address_entity.reset()
        self._hospital_id_generator.reset()
        self._name_generator.reset()
        self._type_generator.reset()
        self._departments_generator.reset()
        self._services_generator.reset()
        self._bed_count_generator.reset()
        self._staff_count_generator.reset()
        self._founding_year_generator.reset()
        self._accreditation_generator.reset()
        self._emergency_services_generator.reset()
        self._teaching_status_generator.reset()
        self._website_generator.reset()
        self._phone_generator.reset()
        self._email_generator.reset()

    def to_dict(self) -> dict[str, Any]:
        """Convert the hospital entity to a dictionary.

        Returns:
            A dictionary containing all hospital properties.
        """
        return {
            "hospital_id": self.hospital_id,
            "name": self.name,
            "type": self.type,
            "departments": self.departments,
            "services": self.services,
            "bed_count": self.bed_count,
            "staff_count": self.staff_count,
            "founding_year": self.founding_year,
            "accreditation": self.accreditation,
            "emergency_services": self.emergency_services,
            "teaching_status": self.teaching_status,
            "website": self.website,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of hospital entities.

        Args:
            count: The number of hospital entities to generate.

        Returns:
            A list of dictionaries containing the generated hospital entities.
        """
        hospitals = []
        for _ in range(count):
            hospitals.append(self.to_dict())
            self.reset()
        return hospitals

    # Property getters
    @property
    def hospital_id(self) -> str:
        """Get the hospital ID.

        Returns:
            A unique identifier for the hospital.
        """
        return self._hospital_id_generator.get()

    @property
    def name(self) -> str:
        """Get the hospital name.

        Returns:
            The hospital name.
        """
        return self._name_generator.get()

    @property
    def type(self) -> str:
        """Get the hospital type.

        Returns:
            The hospital type (e.g., "General", "Specialty", "Teaching").
        """
        return self._type_generator.get()

    @property
    def departments(self) -> list[str]:
        """Get the hospital departments.

        Returns:
            A list of departments in the hospital.
        """
        return self._departments_generator.get()

    @property
    def services(self) -> list[str]:
        """Get the hospital services.

        Returns:
            A list of services offered by the hospital.
        """
        return self._services_generator.get()

    @property
    def bed_count(self) -> int:
        """Get the hospital bed count.

        Returns:
            The number of beds in the hospital.
        """
        return self._bed_count_generator.get()

    @property
    def staff_count(self) -> int:
        """Get the hospital staff count.

        Returns:
            The number of staff members in the hospital.
        """
        return self._staff_count_generator.get()

    @property
    def founding_year(self) -> int:
        """Get the hospital founding year.

        Returns:
            The year the hospital was founded.
        """
        return self._founding_year_generator.get()

    @property
    def accreditation(self) -> list[str]:
        """Get the hospital accreditations.

        Returns:
            A list of accreditations held by the hospital.
        """
        return self._accreditation_generator.get()

    @property
    def emergency_services(self) -> bool:
        """Get whether the hospital offers emergency services.

        Returns:
            True if the hospital offers emergency services, False otherwise.
        """
        return self._emergency_services_generator.get()

    @property
    def teaching_status(self) -> bool:
        """Get whether the hospital is a teaching hospital.

        Returns:
            True if the hospital is a teaching hospital, False otherwise.
        """
        return self._teaching_status_generator.get()

    @property
    def website(self) -> str:
        """Get the hospital website.

        Returns:
            The hospital website URL.
        """
        return self._website_generator.get()

    @property
    def phone(self) -> str:
        """Get the hospital phone number.

        Returns:
            The hospital phone number.
        """
        return self._phone_generator.get()

    @property
    def email(self) -> str:
        """Get the hospital email address.

        Returns:
            The hospital email address.
        """
        return self._email_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the hospital address.

        Returns:
            A dictionary containing the hospital address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_hospital_id(self) -> str:
        """Generate a unique hospital ID.

        Returns:
            A unique hospital ID.
        """
        import uuid

        return f"HOSP-{uuid.uuid4().hex[:8].upper()}"

    def _generate_name(self) -> str:
        """Generate a hospital name.

        Returns:
            A hospital name.
        """
        from datamimic_ce.domains.healthcare.generators.hospital_generator import generate_hospital_name

        city = self._address_entity.city
        state = self._address_entity.state

        return generate_hospital_name(city, state)

    def _generate_type(self) -> str:
        """Generate a hospital type.

        Returns:
            A hospital type.
        """
        import random

        hospital_types = self._data_loader.get_data("hospital_types", self._country_code)
        return random.choice(hospital_types)

    def _generate_departments(self) -> list[str]:
        """Generate a list of hospital departments.

        Returns:
            A list of hospital departments.
        """
        import random

        all_departments = self._data_loader.get_data("departments", self._country_code)

        # Determine how many departments to include
        hospital_type = self.type
        if hospital_type == "Specialty":
            # Specialty hospitals have fewer departments
            num_departments = random.randint(3, 8)
        elif hospital_type == "Community":
            # Community hospitals have a moderate number of departments
            num_departments = random.randint(5, 12)
        else:
            # General and teaching hospitals have more departments
            num_departments = random.randint(10, 20)

        # Select random departments
        departments = random.sample(all_departments, min(num_departments, len(all_departments)))

        # Sort departments alphabetically
        return sorted(departments)

    def _generate_services(self) -> list[str]:
        """Generate a list of hospital services.

        Returns:
            A list of hospital services.
        """
        import random

        all_services = self._data_loader.get_data("services", self._country_code)

        # Determine how many services to include
        hospital_type = self.type
        if hospital_type == "Specialty":
            # Specialty hospitals have fewer services
            num_services = random.randint(5, 10)
        elif hospital_type == "Community":
            # Community hospitals have a moderate number of services
            num_services = random.randint(8, 15)
        else:
            # General and teaching hospitals have more services
            num_services = random.randint(12, 25)

        # Select random services
        services = random.sample(all_services, min(num_services, len(all_services)))

        # Sort services alphabetically
        return sorted(services)

    def _generate_bed_count(self) -> int:
        """Generate a hospital bed count.

        Returns:
            The number of beds in the hospital.
        """
        import random

        hospital_type = self.type
        if hospital_type == "Specialty":
            # Specialty hospitals tend to be smaller
            return random.randint(50, 200)
        elif hospital_type == "Community":
            # Community hospitals are medium-sized
            return random.randint(100, 300)
        elif hospital_type == "Teaching":
            # Teaching hospitals tend to be larger
            return random.randint(300, 1000)
        else:
            # General hospitals vary in size
            return random.randint(100, 500)

    def _generate_staff_count(self) -> int:
        """Generate a hospital staff count.

        Returns:
            The number of staff members in the hospital.
        """
        # Staff count is typically proportional to bed count
        # with a ratio of about 2-4 staff per bed
        import random

        bed_count = self.bed_count
        staff_ratio = random.uniform(2.0, 4.0)

        return int(bed_count * staff_ratio)

    def _generate_founding_year(self) -> int:
        """Generate a hospital founding year.

        Returns:
            The year the hospital was founded.
        """
        import random
        from datetime import datetime

        current_year = datetime.now().year

        # Most hospitals were founded in the last 150 years
        return random.randint(current_year - 150, current_year - 5)

    def _generate_accreditation(self) -> list[str]:
        """Generate a list of hospital accreditations.

        Returns:
            A list of accreditations held by the hospital.
        """
        import random

        all_accreditations = self._data_loader.get_data("accreditations", self._country_code)

        # Determine how many accreditations to include
        num_accreditations = random.randint(1, 4)

        # Select random accreditations
        accreditations = random.sample(all_accreditations, min(num_accreditations, len(all_accreditations)))

        return accreditations

    def _generate_emergency_services(self) -> bool:
        """Generate whether the hospital offers emergency services.

        Returns:
            True if the hospital offers emergency services, False otherwise.
        """
        import random

        hospital_type = self.type
        if hospital_type == "Specialty":
            # Specialty hospitals are less likely to have emergency services
            return random.random() < 0.3
        else:
            # Other hospital types usually have emergency services
            return random.random() < 0.9

    def _generate_teaching_status(self) -> bool:
        """Generate whether the hospital is a teaching hospital.

        Returns:
            True if the hospital is a teaching hospital, False otherwise.
        """
        import random

        hospital_type = self.type
        if hospital_type == "Teaching":
            # Teaching hospitals are always teaching hospitals
            return True
        elif hospital_type == "General":
            # Some general hospitals are teaching hospitals
            return random.random() < 0.3
        else:
            # Other hospital types are rarely teaching hospitals
            return random.random() < 0.1

    def _generate_website(self) -> str:
        """Generate a hospital website URL.

        Returns:
            A hospital website URL.
        """
        # Generate a website based on the hospital name
        name = self.name.lower()

        # Remove common words and special characters
        for word in ["hospital", "medical", "center", "health", "healthcare", "regional", "memorial"]:
            name = name.replace(word, "")

        # Replace spaces and special characters with empty strings
        import re

        name = re.sub(r"[^a-zA-Z0-9]", "", name)

        # If the name is too short, use a generic name
        if len(name) < 3:
            name = f"hospital{self.hospital_id.lower()}"

        # Generate domain extension based on country
        if self._country_code == "US":
            domain = ".org"
        else:
            domain = f".{self._country_code.lower()}"

        return f"https://www.{name}{domain}"

    def _generate_phone(self) -> str:
        """Generate a hospital phone number.

        Returns:
            A hospital phone number.
        """
        import random

        if self._country_code == "US":
            area_code = random.randint(100, 999)
            prefix = random.randint(100, 999)
            line = random.randint(1000, 9999)
            return f"({area_code}) {prefix}-{line}"
        else:
            # Generic international format
            country_code = random.randint(1, 99)
            area_code = random.randint(10, 999)
            number = random.randint(1000000, 9999999)
            return f"+{country_code} {area_code} {number}"

    def _generate_email(self) -> str:
        """Generate a hospital email address.

        Returns:
            A hospital email address.
        """
        # Generate an email based on the hospital name and website
        website = self.website

        # Extract domain from website
        domain = website.replace("https://www.", "")

        return f"info@{domain}"
