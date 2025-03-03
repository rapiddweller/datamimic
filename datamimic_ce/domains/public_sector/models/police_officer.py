# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer entity model.

This module provides the PoliceOfficer entity model for generating realistic police officer data.
"""

from typing import Any, ClassVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import PropertyCache
from datamimic_ce.domains.public_sector.data_loaders.police_loader import PoliceDataLoader


class PoliceOfficer(BaseEntity):
    """Generate police officer data.

    This class generates realistic police officer data including officer IDs,
    names, ranks, departments, badge numbers, employment information, and
    contact details.

    It uses PersonEntity for generating personal information and
    AddressEntity for generating address information.

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
        """Initialize the PoliceOfficer entity.

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
        self._data_loader = PoliceDataLoader()

        # Initialize person entity for personal information
        self._person_entity = self._class_factory_util.get_person_entity(locale=locale, dataset=dataset)

        # Initialize address entity for address information
        self._address_entity = self._class_factory_util.get_address_entity(locale=locale, dataset=dataset)

        # Initialize field generators
        self._initialize_generators()

    def _initialize_generators(self):
        """Initialize all field generators."""
        # Basic information
        self._officer_id_generator = PropertyCache(self._generate_officer_id)
        self._badge_number_generator = PropertyCache(self._generate_badge_number)
        self._rank_generator = PropertyCache(self._generate_rank)
        self._department_generator = PropertyCache(self._generate_department)
        self._unit_generator = PropertyCache(self._generate_unit)
        self._hire_date_generator = PropertyCache(self._generate_hire_date)
        self._years_of_service_generator = PropertyCache(self._generate_years_of_service)
        self._certifications_generator = PropertyCache(self._generate_certifications)
        self._languages_generator = PropertyCache(self._generate_languages)
        self._shift_generator = PropertyCache(self._generate_shift)
        self._email_generator = PropertyCache(self._generate_email)
        self._phone_generator = PropertyCache(self._generate_phone)

    def reset(self) -> None:
        """Reset all field generators, causing new values to be generated on the next access."""
        self._person_entity.reset()
        self._address_entity.reset()
        self._officer_id_generator.reset()
        self._badge_number_generator.reset()
        self._rank_generator.reset()
        self._department_generator.reset()
        self._unit_generator.reset()
        self._hire_date_generator.reset()
        self._years_of_service_generator.reset()
        self._certifications_generator.reset()
        self._languages_generator.reset()
        self._shift_generator.reset()
        self._email_generator.reset()
        self._phone_generator.reset()

    def to_dict(self) -> dict[str, Any]:
        """Convert the police officer entity to a dictionary.

        Returns:
            A dictionary containing all police officer properties.
        """
        return {
            "officer_id": self.officer_id,
            "badge_number": self.badge_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth,
            "age": self.age,
            "rank": self.rank,
            "department": self.department,
            "unit": self.unit,
            "hire_date": self.hire_date,
            "years_of_service": self.years_of_service,
            "certifications": self.certifications,
            "languages": self.languages,
            "shift": self.shift,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of police officer entities.

        Args:
            count: The number of police officer entities to generate.

        Returns:
            A list of dictionaries containing the generated police officer entities.
        """
        officers = []
        for _ in range(count):
            officers.append(self.to_dict())
            self.reset()
        return officers

    # Property getters
    @property
    def officer_id(self) -> str:
        """Get the officer ID.

        Returns:
            A unique identifier for the officer.
        """
        return self._officer_id_generator.get()

    @property
    def badge_number(self) -> str:
        """Get the badge number.

        Returns:
            A badge number.
        """
        return self._badge_number_generator.get()

    @property
    def first_name(self) -> str:
        """Get the officer's first name.

        Returns:
            The officer's first name.
        """
        return self._person_entity.first_name

    @property
    def last_name(self) -> str:
        """Get the officer's last name.

        Returns:
            The officer's last name.
        """
        return self._person_entity.last_name

    @property
    def full_name(self) -> str:
        """Get the officer's full name.

        Returns:
            The officer's full name.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def gender(self) -> str:
        """Get the officer's gender.

        Returns:
            The officer's gender.
        """
        return self._person_entity.gender

    @property
    def date_of_birth(self) -> str:
        """Get the officer's date of birth.

        Returns:
            The officer's date of birth in YYYY-MM-DD format.
        """
        return self._person_entity.date_of_birth

    @property
    def age(self) -> int:
        """Get the officer's age.

        Returns:
            The officer's age in years.
        """
        return self._person_entity.age

    @property
    def rank(self) -> str:
        """Get the officer's rank.

        Returns:
            The officer's rank.
        """
        return self._rank_generator.get()

    @property
    def department(self) -> str:
        """Get the department where the officer works.

        Returns:
            The name of the department.
        """
        return self._department_generator.get()

    @property
    def unit(self) -> str:
        """Get the unit the officer is assigned to.

        Returns:
            The unit name.
        """
        return self._unit_generator.get()

    @property
    def hire_date(self) -> str:
        """Get the date the officer was hired.

        Returns:
            The hire date in YYYY-MM-DD format.
        """
        return self._hire_date_generator.get()

    @property
    def years_of_service(self) -> int:
        """Get the officer's years of service.

        Returns:
            The number of years of service.
        """
        return self._years_of_service_generator.get()

    @property
    def certifications(self) -> list[str]:
        """Get the officer's certifications.

        Returns:
            A list of certifications.
        """
        return self._certifications_generator.get()

    @property
    def languages(self) -> list[str]:
        """Get the languages spoken by the officer.

        Returns:
            A list of languages.
        """
        return self._languages_generator.get()

    @property
    def shift(self) -> str:
        """Get the officer's shift.

        Returns:
            The shift (e.g., 'Day', 'Night', 'Swing').
        """
        return self._shift_generator.get()

    @property
    def email(self) -> str:
        """Get the officer's email address.

        Returns:
            The officer's email address.
        """
        return self._email_generator.get()

    @property
    def phone(self) -> str:
        """Get the officer's phone number.

        Returns:
            The officer's phone number.
        """
        return self._phone_generator.get()

    @property
    def address(self) -> dict[str, Any]:
        """Get the officer's address.

        Returns:
            A dictionary containing the officer's address information.
        """
        return self._address_entity.to_dict()

    # Generator methods
    def _generate_officer_id(self) -> str:
        """Generate a unique officer ID.

        Returns:
            A unique officer ID.
        """
        import uuid

        return f"OFF-{uuid.uuid4().hex[:8].upper()}"

    def _generate_badge_number(self) -> str:
        """Generate a badge number.

        Returns:
            A badge number.
        """
        import random

        return f"{random.randint(1000, 9999)}"

    def _generate_rank(self) -> str:
        """Generate a police rank.

        Returns:
            A police rank.
        """
        import random

        ranks = PoliceDataLoader.load_ranks(self._country_code)
        if not ranks:
            # Default ranks if no data is available
            default_ranks = ["Officer", "Sergeant", "Lieutenant", "Captain", "Chief"]
            return random.choice(default_ranks)

        return ranks[random.randint(0, len(ranks) - 1)].get("rank", "Officer")

    def _generate_department(self) -> str:
        """Generate a police department name.

        Returns:
            A police department name.
        """
        import random

        departments = PoliceDataLoader.load_departments(self._country_code)
        if not departments:
            # Default departments if no data is available
            city_or_county = self._address_entity.city
            default_departments = [f"{city_or_county} Police Department", f"{city_or_county} County Sheriff's Office"]
            return random.choice(default_departments)

        return departments[random.randint(0, len(departments) - 1)].get(
            "name", f"{self._address_entity.city} Police Department"
        )

    def _generate_unit(self) -> str:
        """Generate a police unit name.

        Returns:
            A police unit name.
        """
        import random

        units = [
            "Patrol",
            "Traffic",
            "Detectives",
            "SWAT",
            "K-9",
            "Narcotics",
            "Homicide",
            "Internal Affairs",
            "Community Relations",
            "Juvenile",
            "Cyber Crimes",
            "Evidence",
            "Training",
        ]
        return random.choice(units)

    def _generate_hire_date(self) -> str:
        """Generate a hire date.

        Returns:
            A hire date in YYYY-MM-DD format.
        """
        import datetime
        import random

        # Calculate a reasonable hire date based on years_of_service
        years_of_service = random.randint(1, min(30, self.age - 21))  # Assume minimum age of 21 to join
        current_date = datetime.datetime.now()
        hire_date = current_date - datetime.timedelta(days=years_of_service * 365)
        return hire_date.strftime("%Y-%m-%d")

    def _generate_years_of_service(self) -> int:
        """Generate years of service.

        Returns:
            Years of service.
        """
        import datetime

        # Calculate years of service based on hire date
        hire_date = datetime.datetime.strptime(self.hire_date, "%Y-%m-%d")
        current_date = datetime.datetime.now()
        return (current_date - hire_date).days // 365

    def _generate_certifications(self) -> list[str]:
        """Generate a list of certifications.

        Returns:
            A list of certifications.
        """
        import random

        all_certifications = [
            "Basic Law Enforcement",
            "Advanced Law Enforcement",
            "Firearms Training",
            "Defensive Tactics",
            "Emergency Vehicle Operations",
            "Crisis Intervention",
            "De-escalation Techniques",
            "First Aid/CPR",
            "Narcotics Investigation",
            "Hostage Negotiation",
            "K-9 Handler",
            "SWAT Operations",
            "Cyber Crime Investigation",
            "Crime Scene Investigation",
            "Motorcycle Patrol",
        ]

        num_certifications = random.randint(1, 4)
        return random.sample(all_certifications, num_certifications)

    def _generate_languages(self) -> list[str]:
        """Generate a list of languages spoken.

        Returns:
            A list of languages.
        """
        import random

        languages = ["English"]

        # Chance to add additional languages
        additional_languages = [
            "Spanish",
            "French",
            "German",
            "Chinese",
            "Arabic",
            "Russian",
            "Japanese",
            "Korean",
            "Portuguese",
            "Italian",
        ]
        num_additional = random.randint(0, 2)

        if num_additional > 0:
            languages.extend(random.sample(additional_languages, num_additional))

        return languages

    def _generate_shift(self) -> str:
        """Generate a work shift.

        Returns:
            A shift name.
        """
        import random

        shifts = ["Day Shift (7AM-3PM)", "Evening Shift (3PM-11PM)", "Night Shift (11PM-7AM)", "Rotating Shift"]
        return random.choice(shifts)

    def _generate_email(self) -> str:
        """Generate an email address.

        Returns:
            An email address.
        """
        import random

        # Generate department-based email
        department = self.department.lower()

        # Simplify department name for email domain
        domain = department.replace(" police department", "pd")
        domain = domain.replace(" county sheriff's office", "sheriff")
        domain = domain.replace(" ", "")

        # Create email formats
        email_formats = [
            f"{self.first_name.lower()}.{self.last_name.lower()}@{domain}.gov",
            f"{self.first_name.lower()[0]}{self.last_name.lower()}@{domain}.gov",
            f"{self.badge_number}@{domain}.gov",
            f"{self.last_name.lower()}.{self.badge_number}@{domain}.gov",
        ]

        return random.choice(email_formats)

    def _generate_phone(self) -> str:
        """Generate a phone number.

        Returns:
            A formatted phone number.
        """
        import random

        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line}"
