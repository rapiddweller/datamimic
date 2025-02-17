# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
from pathlib import Path

from mimesis import Datetime, Gender, Person
from mimesis.locales import Locale


def calculate_age(birthdate: datetime.datetime) -> int:
    """Calculate age from birthdate."""
    today = datetime.datetime.now()
    # Normalize both dates to midnight for consistent comparison
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    birthdate = birthdate.replace(hour=0, minute=0, second=0, microsecond=0)

    age = today.year - birthdate.year
    # Create comparison dates without the year to handle edge cases correctly
    today_date = today.replace(year=2000)  # Use a leap year for comparison
    birth_date = birthdate.replace(year=2000)  # Use same year for valid comparison
    if today_date < birth_date:
        age -= 1
    return max(0, age)  # Ensure age is never negative


def get_salutation(salutation_file: Path) -> dict[str, str]:
    """Load salutations from CSV file."""
    try:
        with open(salutation_file) as f:
            lines = f.readlines()
            if not lines:
                return {}
            female, male = lines[0].strip().split(",")
            return {"FEMALE": female, "MALE": male}
    except (FileNotFoundError, IndexError, ValueError):
        return {}


class PersonEntity:
    """Generate personal data using Mimesis.

    This class uses Mimesis to generate realistic personal data with support for multiple locales.

    Supported short codes:
    - US: English (US)
    - GB: English (UK)
    - CN: Chinese
    - BR: Portuguese (Brazil)
    - DE: German

    Full Mimesis locales are also supported, including but not limited to:
    - English: 'en', 'en-au', 'en-ca', 'en-gb'
    - European: 'de', 'fr', 'it', 'es', 'pt', 'nl'
    - Asian: 'zh', 'ja', 'ko'
    - Russian: 'ru'
    - Turkish: 'tr'
    - And many more...

    For a complete list of supported locales, refer to Mimesis documentation:
    https://mimesis.name/en/latest/api.html#locales
    """

    # Internal mapping of short codes to Mimesis locales
    _SHORT_CODES = {
        "US": "en",
        "GB": "en-gb",
        "CN": "zh",
        "BR": "pt-br",
        "DE": "de",
    }

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        count: int = 1,
        min_age: int = 15,
        max_age: int = 105,
        female_quota: float = 0.49,
        other_gender_quota: float = 0.02,
        noble_quota: float = 0.001,
        academic_title_quota: float = 0.5,
        dataset: str | None = None,  # only for our own datasets (not for Mimesis)
    ):
        """Initialize the PersonEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code - can be either a short code (e.g. 'US', 'GB') or Mimesis locale (e.g. 'en', 'de')
            count: Number of entities to generate
            min_age: Minimum age for generated persons
            max_age: Maximum age for generated persons
            female_quota: Proportion of females in generated data
            other_gender_quota: Proportion of other genders in generated data
            noble_quota: Proportion of persons with nobility titles
            academic_title_quota: Proportion of persons with academic titles
        """
        # Convert short codes to Mimesis locales
        # First try the short code mapping
        mimesis_locale = self._SHORT_CODES.get(locale.upper())
        if not mimesis_locale:
            # If not a short code, handle potential underscore format (e.g., 'de_DE' -> 'de')
            mimesis_locale = locale.lower().split("_")[0]
            # For backwards compatibility, map some common codes
            if mimesis_locale == "en":
                mimesis_locale = "en"  # Default English
            elif mimesis_locale == "de":
                mimesis_locale = "de"  # German
            elif mimesis_locale == "fr":
                mimesis_locale = "fr"  # French
            # Add more mappings as needed

        self._locale = mimesis_locale
        self._min_age = min_age
        self._max_age = max_age
        self._female_quota = female_quota
        self._other_gender_quota = other_gender_quota
        self._noble_quota = noble_quota
        self._academic_title_quota = academic_title_quota

        # Initialize Mimesis generators
        self._person = Person(Locale(self._locale))
        self._datetime = Datetime()

        # Initialize cached values
        self._cached_gender: str | None = None
        self._cached_birthdate: datetime.datetime | None = None
        self._cached_given_name: str | None = None
        self._cached_family_name: str | None = None
        self._cached_email: str | None = None
        self._cached_academic_title: str | None = None
        self._cached_nobility_title: str | None = None
        self._cached_username: str | None = None
        self._cached_password: str | None = None
        self._cached_phone: str | None = None
        self._cached_height: float | None = None
        self._cached_weight: int | None = None
        self._cached_blood_type: str | None = None
        self._cached_occupation: str | None = None
        self._cached_nationality: str | None = None
        self._cached_university: str | None = None
        self._cached_language: str | None = None
        self._cached_academic_degree: str | None = None

    def _generate_gender(self) -> str:
        """Generate gender based on configured quotas."""
        if self._cached_gender is None:
            rand = self._person.random.random()
            if rand < self._female_quota:
                self._cached_gender = "female"
            elif rand < (self._female_quota + self._other_gender_quota):
                self._cached_gender = "other"
            else:
                self._cached_gender = "male"
        return self._cached_gender

    def _generate_birthdate(self) -> datetime.datetime:
        """Generate a birthdate within the configured age range."""
        if self._cached_birthdate is None:
            today = datetime.datetime.now()

            # Keep generating until we get a valid birthdate
            while True:
                # Calculate date range for the birthdate
                min_year = today.year - self._max_age
                max_year = today.year - self._min_age

                # Generate random date within the range
                year = self._person.random.randint(min_year, max_year)
                month = self._person.random.randint(1, 12)
                max_day = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
                if month == 2:
                    max_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                day = self._person.random.randint(1, max_day)

                # Create the birthdate
                birthdate = datetime.datetime(year, month, day)
                age = calculate_age(birthdate)

                # Only accept if the age is within range
                if self._min_age <= age <= self._max_age:
                    self._cached_birthdate = birthdate
                    break

        return self._cached_birthdate

    def _generate_given_name(self) -> str:
        """Generate a given name based on gender."""
        if self._cached_given_name is None:
            gender = self._generate_gender()
            if gender == "other":
                # For "other" gender, randomly choose between male and female names
                gender = "male" if self._person.random.random() < 0.5 else "female"
            mimesis_gender = Gender.FEMALE if gender == "female" else Gender.MALE
            self._cached_given_name = self._person.first_name(gender=mimesis_gender)
        return self._cached_given_name

    def _generate_family_name(self) -> str:
        """Generate a family name."""
        if self._cached_family_name is None:
            self._cached_family_name = self._person.last_name()
        return self._cached_family_name

    def _generate_email(self) -> str:
        """Generate an email address."""
        if self._cached_email is None:
            self._cached_email = self._person.email(domains=["example.com"])
        return self._cached_email

    def _generate_academic_title(self) -> str:
        """Generate an academic title if appropriate."""
        if self._cached_academic_title is None:
            if self.age < 20 or self._person.random.random() > self._academic_title_quota:
                self._cached_academic_title = ""
            else:
                self._cached_academic_title = "Dr."  # Simplified for testing
        return self._cached_academic_title

    def _generate_nobility_title(self) -> str:
        """Generate a nobility title if appropriate."""
        if self._cached_nobility_title is None:
            if self._person.random.random() > self._noble_quota:
                self._cached_nobility_title = ""
            else:
                gender = self._generate_gender()
                if gender == "female":
                    self._cached_nobility_title = "Baroness"
                elif gender == "male":
                    self._cached_nobility_title = "Baron"
                else:
                    self._cached_nobility_title = ""
        return self._cached_nobility_title

    def _generate_username(self) -> str:
        """Generate a username."""
        if self._cached_username is None:
            self._cached_username = self._person.username(mask="ld")
        return self._cached_username

    def _generate_password(self, length: int = 12) -> str:
        """Generate a secure password.

        Args:
            length: Minimum length of the password (default: 12)

        Returns:
            A secure password containing uppercase, lowercase, digits, and special characters.
        """
        if self._cached_password is None:
            # Keep generating until we get a password that meets all requirements
            while True:
                password = self._person.password(length=length)
                # Check if password meets all requirements
                has_upper = any(c.isupper() for c in password)
                has_lower = any(c.islower() for c in password)
                has_digit = any(c.isdigit() for c in password)
                has_special = any(not c.isalnum() for c in password)

                if has_upper and has_lower and has_digit and has_special:
                    self._cached_password = password
                    break
        return self._cached_password

    def _generate_phone(self) -> str:
        """Generate a phone number."""
        if self._cached_phone is None:
            self._cached_phone = self._person.phone_number()
        return self._cached_phone

    def _generate_height(self) -> float:
        """Generate height in meters."""
        if self._cached_height is None:
            self._cached_height = float(self._person.height())
        return self._cached_height

    def _generate_weight(self) -> int:
        """Generate weight in kg."""
        if self._cached_weight is None:
            self._cached_weight = self._person.weight()
        return self._cached_weight

    def _generate_blood_type(self) -> str:
        """Generate blood type."""
        if self._cached_blood_type is None:
            self._cached_blood_type = self._person.blood_type()
        return self._cached_blood_type

    def _generate_occupation(self) -> str:
        """Generate occupation."""
        if self._cached_occupation is None:
            self._cached_occupation = self._person.occupation()
        return self._cached_occupation

    def _generate_nationality(self) -> str:
        """Generate nationality."""
        if self._cached_nationality is None:
            gender = self._generate_gender()
            mimesis_gender = Gender.FEMALE if gender == "female" else Gender.MALE
            self._cached_nationality = self._person.nationality(gender=mimesis_gender)
        return self._cached_nationality

    def _generate_university(self) -> str:
        """Generate university name."""
        if self._cached_university is None:
            self._cached_university = self._person.university()
        return self._cached_university

    def _generate_language(self) -> str:
        """Generate spoken language."""
        if self._cached_language is None:
            self._cached_language = self._person.language()
        return self._cached_language

    def _generate_academic_degree(self) -> str:
        """Generate academic degree."""
        if self._cached_academic_degree is None:
            self._cached_academic_degree = self._person.academic_degree()
        return self._cached_academic_degree

    def reset(self) -> None:
        """Reset all cached values."""
        self._cached_gender = None
        self._cached_birthdate = None
        self._cached_given_name = None
        self._cached_family_name = None
        self._cached_email = None
        self._cached_academic_title = None
        self._cached_nobility_title = None
        self._cached_username = None
        self._cached_password = None
        self._cached_phone = None
        self._cached_height = None
        self._cached_weight = None
        self._cached_blood_type = None
        self._cached_occupation = None
        self._cached_nationality = None
        self._cached_university = None
        self._cached_language = None
        self._cached_academic_degree = None

    @property
    def gender(self) -> str:
        """Get the person's gender."""
        return self._generate_gender()

    @property
    def birthdate(self) -> datetime.datetime:
        """Get the person's birthdate."""
        return self._generate_birthdate()

    @property
    def given_name(self) -> str:
        """Get the person's given name."""
        return self._generate_given_name()

    @property
    def family_name(self) -> str:
        """Get the person's family name."""
        return self._generate_family_name()

    @property
    def name(self) -> str:
        """Get the person's full name."""
        return f"{self.given_name} {self.family_name}"

    @property
    def email(self) -> str:
        """Get the person's email address."""
        return self._generate_email()

    @property
    def academic_title(self) -> str:
        """Get the person's academic title."""
        return self._generate_academic_title()

    @property
    def age(self) -> int:
        """Get the person's age."""
        return calculate_age(self.birthdate)

    @property
    def salutation(self) -> str:
        """Get the person's salutation."""
        gender = self.gender
        if gender == "female":
            return "Mrs."
        elif gender == "male":
            return "Mr."
        return ""

    @property
    def nobility_title(self) -> str:
        """Get the person's nobility title."""
        return self._generate_nobility_title()

    @property
    def username(self) -> str:
        """Get the person's username."""
        return self._generate_username()

    @property
    def password(self) -> str:
        """Get the person's password."""
        return self._generate_password()

    @property
    def phone(self) -> str:
        """Get the person's phone number."""
        return self._generate_phone()

    @property
    def height(self) -> float:
        """Get the person's height in meters."""
        return self._generate_height()

    @property
    def weight(self) -> int:
        """Get the person's weight in kg."""
        return self._generate_weight()

    @property
    def blood_type(self) -> str:
        """Get the person's blood type."""
        return self._generate_blood_type()

    @property
    def occupation(self) -> str:
        """Get the person's occupation."""
        return self._generate_occupation()

    @property
    def nationality(self) -> str:
        """Get the person's nationality."""
        return self._generate_nationality()

    @property
    def university(self) -> str:
        """Get the person's university."""
        return self._generate_university()

    @property
    def language(self) -> str:
        """Get the person's spoken language."""
        return self._generate_language()

    @property
    def academic_degree(self) -> str:
        """Get the person's academic degree."""
        return self._generate_academic_degree()
