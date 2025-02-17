# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from mimesis import Address
from mimesis.enums import CountryCode
from mimesis.locales import Locale


class AddressEntity:
    """Generate address data using Mimesis.

    This class uses Mimesis to generate realistic address data with support for multiple locales.

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

    Available Properties:
    - Basic Address: street, house_number, city, state, postal_code/zip_code
    - Location: country, country_code, coordinates, continent, latitude, longitude
    - Contact: office_phone, private_phone, mobile_phone, fax
    - Organization: organization
    - Region Info: area, state_abbr, federal_subject, prefecture, province, region
    - Codes: calling_code/isd_code, iata_code, icao_code
    - Full Address: formatted_address
    """

    # Internal mapping of short codes to Mimesis locales
    _SHORT_CODES = {
        "US": "en",
        "GB": "en-gb",
        "CN": "zh",
        "BR": "pt-br",
        "DE": "de",
    }

    def __init__(self, class_factory_util, locale: str = "en", dataset: str | None = None):
        """Initialize the AddressEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code - can be either a short code (e.g. 'US', 'GB') or Mimesis locale (e.g. 'en', 'de')
            dataset: Legacy parameter for backward compatibility
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

        # Initialize Mimesis generator
        self._address = Address(Locale(self._locale))

        # Initialize cached values
        self._cached_street: str | None = None
        self._cached_house_number: str | None = None
        self._cached_city: str | None = None
        self._cached_state: str | None = None
        self._cached_postal_code: str | None = None
        self._cached_country: str | None = None
        self._cached_country_code: str | None = None
        self._cached_office_phone: str | None = None
        self._cached_private_phone: str | None = None
        self._cached_mobile_phone: str | None = None
        self._cached_fax: str | None = None
        self._cached_organization: str | None = None
        self._cached_coordinates: dict[str, str | float] | None = None
        # New cached values
        self._cached_state_abbr: str | None = None
        self._cached_continent: str | None = None
        self._cached_calling_code: str | None = None
        self._cached_iata_code: str | None = None
        self._cached_icao_code: str | None = None
        self._cached_formatted_address: str | None = None
        self._cached_latitude: float | None = None
        self._cached_longitude: float | None = None

    def _generate_street(self) -> str:
        """Generate a street name."""
        if self._cached_street is None:
            self._cached_street = self._address.street_name()
        return self._cached_street

    def _generate_house_number(self) -> str:
        """Generate a house number."""
        if self._cached_house_number is None:
            self._cached_house_number = self._address.street_number()
        return self._cached_house_number

    def _generate_city(self) -> str:
        """Generate a city name."""
        if self._cached_city is None:
            self._cached_city = self._address.city()
        return self._cached_city

    def _generate_state(self) -> str:
        """Generate a state name."""
        if self._cached_state is None:
            self._cached_state = self._address.state()
        return self._cached_state

    def _generate_postal_code(self) -> str:
        """Generate a postal code."""
        if self._cached_postal_code is None:
            self._cached_postal_code = self._address.postal_code()
        return self._cached_postal_code

    def _generate_country(self) -> str:
        """Generate a country name."""
        if self._cached_country is None:
            self._cached_country = self._address.country()
        return self._cached_country

    def _generate_country_code(self) -> str:
        """Generate a country code."""
        if self._cached_country_code is None:
            self._cached_country_code = self._address.country_code(code=CountryCode.A2)
        return self._cached_country_code

    def _generate_phone(self) -> str:
        """Generate a phone number with area code.

        Returns:
            A phone number in the format: (+XXX) XXX-XXX-XXXX
        """
        # Format: (+XXX) XXX-XXX-XXXX
        calling_code = str(abs(int(self._address.calling_code().strip("+")))).zfill(3)[:3]  # Ensure exactly 3 digits
        area = str(self._address.random.randint(100, 999))  # Always 3 digits
        local_1 = str(self._address.random.randint(100, 999))  # Always 3 digits
        local_2 = str(self._address.random.randint(1000, 9999))  # Always 4 digits
        return f"(+{calling_code}) {area}-{local_1}-{local_2}"

    def _generate_organization(self) -> str:
        """Generate an organization name."""
        if self._cached_organization is None:
            # Use city name plus a common business suffix
            suffixes = ["Inc.", "Ltd.", "LLC", "Corp.", "Group", "Holdings"]
            city = self._generate_city()
            suffix = self._address.random.choice(suffixes)
            self._cached_organization = f"{city} {suffix}"
        return self._cached_organization

    def _generate_coordinates(self) -> dict[str, str | float]:
        """Generate geographical coordinates."""
        if self._cached_coordinates is None:
            self._cached_coordinates = self._address.coordinates()
        return self._cached_coordinates

    def _generate_state_abbr(self) -> str:
        """Generate a state abbreviation."""
        if self._cached_state_abbr is None:
            self._cached_state_abbr = self._address.state(abbr=True)
        return self._cached_state_abbr

    def _generate_continent(self) -> str:
        """Generate a continent name."""
        if self._cached_continent is None:
            self._cached_continent = self._address.continent()
        return self._cached_continent

    def _generate_calling_code(self) -> str:
        """Generate a calling code."""
        if self._cached_calling_code is None:
            self._cached_calling_code = self._address.calling_code()
        return self._cached_calling_code

    def _generate_iata_code(self) -> str:
        """Generate an IATA airport code."""
        if self._cached_iata_code is None:
            self._cached_iata_code = self._address.iata_code()
        return self._cached_iata_code

    def _generate_icao_code(self) -> str:
        """Generate an ICAO airport code."""
        if self._cached_icao_code is None:
            self._cached_icao_code = self._address.icao_code()
        return self._cached_icao_code

    def _generate_formatted_address(self) -> str:
        """Generate a formatted full address."""
        if self._cached_formatted_address is None:
            self._cached_formatted_address = self._address.address()
        return self._cached_formatted_address

    def reset(self) -> None:
        """Reset all cached values."""
        self._cached_street = None
        self._cached_house_number = None
        self._cached_city = None
        self._cached_state = None
        self._cached_postal_code = None
        self._cached_country = None
        self._cached_country_code = None
        self._cached_office_phone = None
        self._cached_private_phone = None
        self._cached_mobile_phone = None
        self._cached_fax = None
        self._cached_organization = None
        self._cached_coordinates = None
        self._cached_state_abbr = None
        self._cached_continent = None
        self._cached_calling_code = None
        self._cached_iata_code = None
        self._cached_icao_code = None
        self._cached_formatted_address = None
        self._cached_latitude = None
        self._cached_longitude = None

    @property
    def street(self) -> str:
        """Get the street name."""
        return self._generate_street()

    @property
    def house_number(self) -> str:
        """Get the house number."""
        return self._generate_house_number()

    @property
    def city(self) -> str:
        """Get the city name."""
        return self._generate_city()

    @property
    def state(self) -> str:
        """Get the state name."""
        return self._generate_state()

    @property
    def postal_code(self) -> str:
        """Get the postal code."""
        return self._generate_postal_code()

    @property
    def zip_code(self) -> str:
        """Get the zip code (alias for postal_code)."""
        return self.postal_code

    @property
    def country(self) -> str:
        """Get the country name."""
        return self._generate_country()

    @property
    def country_code(self) -> str:
        """Get the country code."""
        return self._generate_country_code()

    @property
    def office_phone(self) -> str:
        """Get the office phone number."""
        if self._cached_office_phone is None:
            self._cached_office_phone = self._generate_phone()
        return self._cached_office_phone

    @property
    def private_phone(self) -> str:
        """Get the private phone number."""
        if self._cached_private_phone is None:
            self._cached_private_phone = self._generate_phone()
        return self._cached_private_phone

    @property
    def mobile_phone(self) -> str:
        """Get the mobile phone number."""
        if self._cached_mobile_phone is None:
            self._cached_mobile_phone = self._generate_phone()
        return self._cached_mobile_phone

    @property
    def fax(self) -> str:
        """Get the fax number."""
        if self._cached_fax is None:
            self._cached_fax = self._generate_phone()
        return self._cached_fax

    @property
    def organization(self) -> str:
        """Get the organization name."""
        return self._generate_organization()

    @property
    def coordinates(self) -> dict[str, str | float]:
        """Get the coordinates."""
        return self._generate_coordinates()

    @property
    def latitude(self) -> float:
        """Get the latitude."""
        coords = self._generate_coordinates()
        return float(coords["latitude"])

    @property
    def longitude(self) -> float:
        """Get the longitude."""
        coords = self._generate_coordinates()
        return float(coords["longitude"])

    @property
    def state_abbr(self) -> str:
        """Get the state abbreviation (e.g., 'CA' for California)."""
        return self._generate_state_abbr()

    @property
    def continent(self) -> str:
        """Get the continent name."""
        return self._generate_continent()

    @property
    def calling_code(self) -> str:
        """Get the country calling code (e.g., '+1' for USA)."""
        return self._generate_calling_code()

    @property
    def isd_code(self) -> str:
        """Get the ISD code (alias for calling_code)."""
        return self.calling_code

    @property
    def iata_code(self) -> str:
        """Get an IATA airport code (e.g., 'LAX' for Los Angeles)."""
        return self._generate_iata_code()

    @property
    def icao_code(self) -> str:
        """Get an ICAO airport code (e.g., 'KLAX' for Los Angeles)."""
        return self._generate_icao_code()

    @property
    def formatted_address(self) -> str:
        """Get a complete formatted address according to locale format."""
        return self._generate_formatted_address()

    @property
    def federal_subject(self) -> str:
        """Get the federal subject (alias for state, used in some countries like Russia)."""
        return self.state

    @property
    def prefecture(self) -> str:
        """Get the prefecture (alias for state, used in some countries like Japan)."""
        return self.state

    @property
    def province(self) -> str:
        """Get the province (alias for state, used in many countries)."""
        return self.state

    @property
    def region(self) -> str:
        """Get the region (alias for state, used in many countries)."""
        return self.state

    @property
    def area(self) -> str:
        """Get the area code (derived from phone number)."""
        # Extract area code from phone number if possible
        phone = self.office_phone
        if "(" in phone and ")" in phone:
            return phone[phone.find("(") + 1 : phone.find(")")]
        return ""
