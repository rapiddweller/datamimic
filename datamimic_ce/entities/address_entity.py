# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.entities.city_entity import CityEntity
from datamimic_ce.entities.country_entity import CountryEntity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.generators.street_name_generator import StreetNameGenerator
from datamimic_ce.logger import logger


class AddressEntity:
    """Generate address data using high-quality datasets.

    This class uses internal datasets to generate realistic address data with support for multiple locales.

    Supported short codes correspond to ISO country codes like:
    - US: United States
    - GB: United Kingdom
    - DE: Germany
    - FR: France
    - IT: Italy
    ...and many more (47 countries in total)

    Full locale codes are also supported, including but not limited to:
    - English: 'en', 'en-au', 'en-ca', 'en-gb'
    - European: 'de', 'fr', 'it', 'es', 'pt', 'nl'
    - Asian: 'zh', 'ja', 'ko', 'th', 'vi'
    - Russian: 'ru'
    - Turkish: 'tr'
    - And many more...

    Available Properties:
    - Basic Address: street, house_number, city, state, postal_code/zip_code
    - Location: country, country_code, coordinates, continent, latitude, longitude
    - Contact: office_phone, private_phone, mobile_phone, fax
    - Organization: organization
    - Region Info: area, state_abbr, federal_subject, prefecture, province, region
    - Codes: calling_code/isd_code, iata_code, icao_code
    - Full Address: formatted_address
    """

    # Complete list of supported datasets (corresponding to ISO country codes)
    _SUPPORTED_DATASETS = {
        "AD",
        "AL",
        "AT",
        "AU",
        "BA",
        "BE",
        "BG",
        "BR",
        "CA",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LI",
        "LT",
        "LU",
        "LV",
        "MC",
        "NL",
        "NO",
        "NZ",
        "PL",
        "PT",
        "RO",
        "RU",
        "SE",
        "SI",
        "SK",
        "SM",
        "TH",
        "TR",
        "UA",
        "US",
        "VA",
        "VE",
        "VN",
    }

    # Common language code to country mapping
    _LANGUAGE_TO_COUNTRY = {
        "en": "US",  # English -> United States
        "de": "DE",  # German -> Germany
        "fr": "FR",  # French -> France
        "es": "ES",  # Spanish -> Spain
        "it": "IT",  # Italian -> Italy
        "pt": "PT",  # Portuguese -> Portugal (not BR to be consistent with country code)
        "ru": "RU",  # Russian -> Russia
        "zh": "CN",  # Chinese -> China (Note: CN not in supported datasets)
        "ja": "JP",  # Japanese -> Japan (Note: JP not in supported datasets)
        "nl": "NL",  # Dutch -> Netherlands
        "sv": "SE",  # Swedish -> Sweden
        "no": "NO",  # Norwegian -> Norway
        "fi": "FI",  # Finnish -> Finland
        "da": "DK",  # Danish -> Denmark
        "pl": "PL",  # Polish -> Poland
        "cs": "CZ",  # Czech -> Czech Republic
        "sk": "SK",  # Slovak -> Slovakia
        "hu": "HU",  # Hungarian -> Hungary
        "ro": "RO",  # Romanian -> Romania
        "bg": "BG",  # Bulgarian -> Bulgaria
        "el": "GR",  # Greek -> Greece
        "tr": "TR",  # Turkish -> Turkey
        "th": "TH",  # Thai -> Thailand
        "vi": "VN",  # Vietnamese -> Vietnam
    }

    # Default fallback dataset
    _DEFAULT_DATASET = "US"

    def __init__(self, class_factory_util, locale: str = "en", dataset: str | None = None):
        """Initialize the AddressEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code - can be either a country code (e.g. 'US', 'GB') or language code (e.g. 'en', 'de')
            dataset: If provided, overrides the locale parameter
        """
        # Store the original locale for backward compatibility with tests
        self._locale = locale

        # Determine the dataset to use
        # Use provided dataset, or resolve from locale, with US as ultimate fallback
        self._target_dataset = dataset if dataset else self._resolve_dataset(locale)

        # Store the data generation utility for later use (avoid repeated method calls)
        self._data_generation_util = class_factory_util.get_data_generation_util()

        # Initialize generators and entities
        self._street_name_gen = StreetNameGenerator(dataset=self._target_dataset)
        self._city_entity = CityEntity(class_factory_util, dataset=self._target_dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._target_dataset)
        self._company_name_generator = CompanyNameGenerator()
        self._country_entity = CountryEntity(class_factory_util)

        # Initialize field generators with optimized lambda functions
        generator_fn_dict = {
            "organization": lambda: self._company_name_generator.generate(),
            "office_phone": lambda: self._phone_number_generator.generate(),
            "private_phone": lambda: self._phone_number_generator.generate(),
            "mobile_phone": lambda: self._phone_number_generator.generate(),
            "fax": lambda: self._phone_number_generator.generate(),
            "street": lambda: self._street_name_gen.generate(),
            "house_number": lambda: str(self._data_generation_util.rnd_int(1, 9999)),
            "city_entity": lambda: self._city_entity,
            # Cache coordinates as they're expensive to generate
            "coordinates": lambda: {
                "latitude": self._data_generation_util.rnd_float(-90, 90),
                "longitude": self._data_generation_util.rnd_float(-180, 180),
            },
        }
        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

        # Initialize cached values for properties not directly from generators
        self._cached_formatted_address: str | None = None
        self._cached_latitude: float | None = None
        self._cached_longitude: float | None = None
        self._cached_continent: str | None = None
        self._cached_iata_code: str | None = None
        self._cached_icao_code: str | None = None
        self._cached_calling_code: str | None = None

        # Keep track of the current city row for optimization
        self._current_city_row = None
        self._current_city_entity = None

    def _resolve_dataset(self, locale: str) -> str:
        """Resolve the locale string to a dataset identifier.

        Args:
            locale: Locale code to resolve

        Returns:
            The dataset identifier to use
        """
        # Handle empty or None values
        if not locale:
            return self._DEFAULT_DATASET

        # Check if the locale is already a supported dataset (country code)
        if locale.upper() in self._SUPPORTED_DATASETS:
            return locale.upper()

        # Handle common locale formats with language and country parts
        parts = locale.lower().split("_" if "_" in locale else "-")

        # If locale includes a country code (e.g., en_US, de-DE)
        if len(parts) > 1 and parts[1].upper() in self._SUPPORTED_DATASETS:
            return parts[1].upper()

        # Try to map the language to a country
        primary_locale = parts[0]
        dataset = self._LANGUAGE_TO_COUNTRY.get(primary_locale)

        # If we found a mapping and it's supported, use it
        if dataset and dataset in self._SUPPORTED_DATASETS:
            return dataset

        # Special cases for common language variants
        if primary_locale == "en":
            return "US"  # Default English to US
        if primary_locale == "pt":
            return "BR" if "BR" in self._SUPPORTED_DATASETS else "PT"  # Try Brazilian Portuguese

        # Log warning about unsupported dataset
        supported_datasets_str = ", ".join(sorted(self._SUPPORTED_DATASETS))
        logger.warning(
            f"Unsupported locale/dataset: {locale}. Using default '{self._DEFAULT_DATASET}' instead. "
            f"Supported datasets are: {supported_datasets_str}"
        )

        return self._DEFAULT_DATASET

    def _get_city_entity(self):
        """Get the cached city entity.

        This method optimizes repeated access to city entity by caching it.

        Returns:
            The current city entity
        """
        if self._current_city_entity is None:
            self._current_city_entity = self._field_generator["city_entity"].get()
        return self._current_city_entity

    def _get_city_row(self):
        """Get the cached city row.

        This method optimizes repeated access to city row by caching it.

        Returns:
            The current city row
        """
        if self._current_city_row is None:
            city_entity = self._get_city_entity()
            self._current_city_row = city_entity._field_generator["city_row"].get()
        return self._current_city_row

    @property
    def street(self) -> str:
        """Get the street name."""
        return self._field_generator["street"].get()

    @property
    def house_number(self) -> str:
        """Get the house number."""
        return self._field_generator["house_number"].get()

    @property
    def city(self) -> str:
        """Get the city name."""
        city_entity = self._get_city_entity()
        city_row = self._get_city_row()
        name_idx = city_entity._city_header_dict.get("name")
        return city_row[name_idx] if name_idx is not None else ""

    @property
    def state(self) -> str:
        """Get the state name."""
        city_entity = self._get_city_entity()
        city_row = self._get_city_row()
        state_id_idx = city_entity._city_header_dict.get("state.id")
        if state_id_idx is not None:
            state_id = city_row[state_id_idx]
            return city_entity._state_dict.get(state_id, "")
        return ""

    @property
    def postal_code(self) -> str:
        """Get the postal code."""
        city_entity = self._get_city_entity()
        city_row = self._get_city_row()
        postal_code_idx = city_entity._city_header_dict.get("postalCode")
        return city_row[postal_code_idx] if postal_code_idx is not None else ""

    @property
    def zip_code(self) -> str:
        """Get the zip code (alias for postal_code)."""
        return self.postal_code

    @property
    def country(self) -> str:
        """Get the country name."""
        return self._get_city_entity()._country

    @property
    def country_code(self) -> str:
        """Get the country code."""
        return self._target_dataset

    @property
    def office_phone(self) -> str:
        """Get the office phone number."""
        return self._field_generator["office_phone"].get()

    @property
    def private_phone(self) -> str:
        """Get the private phone number."""
        return self._field_generator["private_phone"].get()

    @property
    def mobile_phone(self) -> str:
        """Get the mobile phone number."""
        return self._field_generator["mobile_phone"].get()

    @property
    def fax(self) -> str:
        """Get the fax number."""
        return self._field_generator["fax"].get()

    @property
    def organization(self) -> str:
        """Get the organization name."""
        return self._field_generator["organization"].get()

    @property
    def coordinates(self) -> dict[str, float]:
        """Get the coordinates."""
        return self._field_generator["coordinates"].get()

    @property
    def latitude(self) -> float:
        """Get the latitude."""
        if self._cached_latitude is None:
            self._cached_latitude = self.coordinates["latitude"]
        assert self._cached_latitude is not None  # Ensure non-None for type checker
        return self._cached_latitude

    @property
    def longitude(self) -> float:
        """Get the longitude."""
        if self._cached_longitude is None:
            self._cached_longitude = self.coordinates["longitude"]
        assert self._cached_longitude is not None  # Ensure non-None for type checker
        return self._cached_longitude

    @property
    def state_abbr(self) -> str:
        """Get the state abbreviation (e.g., 'CA' for California)."""
        city_entity = self._get_city_entity()
        city_row = self._get_city_row()
        state_id_idx = city_entity._city_header_dict.get("state.id")
        return city_row[state_id_idx] if state_id_idx is not None else ""

    @property
    def continent(self) -> str:
        """Get the continent name."""
        if self._cached_continent is None:
            # Map country codes to continents (simplified)
            continent_map = {
                # North America
                "US": "North America",
                "CA": "North America",
                # South America
                "BR": "South America",
                "VE": "South America",
                # Europe - most of our supported datasets
                "AD": "Europe",
                "AL": "Europe",
                "AT": "Europe",
                "BA": "Europe",
                "BE": "Europe",
                "BG": "Europe",
                "CH": "Europe",
                "CY": "Europe",
                "CZ": "Europe",
                "DE": "Europe",
                "DK": "Europe",
                "EE": "Europe",
                "ES": "Europe",
                "FI": "Europe",
                "FR": "Europe",
                "GB": "Europe",
                "GR": "Europe",
                "HR": "Europe",
                "HU": "Europe",
                "IE": "Europe",
                "IS": "Europe",
                "IT": "Europe",
                "LI": "Europe",
                "LT": "Europe",
                "LU": "Europe",
                "LV": "Europe",
                "MC": "Europe",
                "NL": "Europe",
                "NO": "Europe",
                "PL": "Europe",
                "PT": "Europe",
                "RO": "Europe",
                "RU": "Europe",
                "SE": "Europe",
                "SI": "Europe",
                "SK": "Europe",
                "SM": "Europe",
                "TR": "Europe",
                "UA": "Europe",
                "VA": "Europe",
                # Asia
                "CN": "Asia",
                "JP": "Asia",
                "TH": "Asia",
                "VN": "Asia",
                # Oceania
                "AU": "Oceania",
                "NZ": "Oceania",
            }
            self._cached_continent = continent_map.get(self.country_code, "Unknown")
        assert self._cached_continent is not None  # Ensure non-None for type checker
        return self._cached_continent

    @property
    def calling_code(self) -> str:
        """Get the country calling code (e.g., '+1' for USA)."""
        if self._cached_calling_code is None:
            # Common calling codes
            code_map = {
                # North America
                "US": "+1",
                "CA": "+1",
                # Europe
                "GB": "+44",
                "DE": "+49",
                "FR": "+33",
                "IT": "+39",
                "ES": "+34",
                "AT": "+43",
                "BE": "+32",
                "BG": "+359",
                "CH": "+41",
                "CZ": "+420",
                "DK": "+45",
                "FI": "+358",
                "GR": "+30",
                "HU": "+36",
                "IE": "+353",
                "LI": "+423",
                "LU": "+352",
                "NL": "+31",
                "NO": "+47",
                "PL": "+48",
                "PT": "+351",
                "RO": "+40",
                "RU": "+7",
                "SE": "+46",
                "SK": "+421",
                "VA": "+39",
                # Asia
                "CN": "+86",
                "JP": "+81",
                "TH": "+66",
                "VN": "+84",
                # Oceania
                "AU": "+61",
                "NZ": "+64",
                # South America
                "BR": "+55",
                "VE": "+58",
            }

            # If the country code is not in our map, try to get it from the CountryEntity
            if self.country_code in code_map:
                self._cached_calling_code = code_map[self.country_code]
            else:
                # Try to get from country entity
                country_data = CountryEntity.get_by_iso_code(self.country_code)
                if country_data and country_data[2]:  # Check for phone code in country data
                    self._cached_calling_code = f"+{country_data[2]}"
                else:
                    self._cached_calling_code = "+"  # Default empty code

        assert self._cached_calling_code is not None  # Ensure non-None for type checker
        return self._cached_calling_code

    @property
    def isd_code(self) -> str:
        """Get the ISD code (alias for calling_code)."""
        return self.calling_code

    @property
    def iata_code(self) -> str:
        """Get an IATA airport code (e.g., 'LAX' for Los Angeles)."""
        if self._cached_iata_code is None:
            # Generate a random 3-letter code as placeholder
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            self._cached_iata_code = "".join(self._data_generation_util.rnd_choice(letters) for _ in range(3))
        assert self._cached_iata_code is not None  # Ensure non-None for type checker
        return self._cached_iata_code

    @property
    def icao_code(self) -> str:
        """Get an ICAO airport code (e.g., 'KLAX' for Los Angeles)."""
        if self._cached_icao_code is None:
            # Generate a random 4-letter code as placeholder
            # Often starts with a region identifier
            region_codes = {
                # North America
                "US": "K",
                "CA": "C",
                # Europe
                "GB": "EG",
                "DE": "ED",
                "FR": "LF",
                "IT": "LI",
                "ES": "LE",
                "AT": "LO",
                "BE": "EB",
                "CH": "LS",
                "CZ": "LK",
                "DK": "EK",
                "FI": "EF",
                "GR": "LG",
                "HU": "LH",
                "IE": "EI",
                "NL": "EH",
                "NO": "EN",
                "PL": "EP",
                "PT": "LP",
                "RO": "LR",
                "RU": "U",
                "SE": "ES",
                "TR": "LT",
                # Asia
                "CN": "Z",
                "JP": "RJ",
                "TH": "VT",
                "VN": "VV",
                # Oceania
                "AU": "Y",
                "NZ": "NZ",
            }

            prefix = region_codes.get(self.country_code, "")

            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            remaining_length = 4 - len(prefix)
            self._cached_icao_code = prefix + "".join(
                self._data_generation_util.rnd_choice(letters) for _ in range(remaining_length)
            )
        assert self._cached_icao_code is not None  # Ensure non-None for type checker
        return self._cached_icao_code

    @property
    def formatted_address(self) -> str:
        """Get a complete formatted address according to locale format."""
        if self._cached_formatted_address is None:
            # Format by region
            country_code = self.country_code

            # North American format
            if country_code in {"US", "CA"}:
                self._cached_formatted_address = (
                    f"{self.house_number} {self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"
                )

            # UK format
            elif country_code == "GB":
                self._cached_formatted_address = (
                    f"{self.house_number} {self.street}, {self.city}, {self.state}, {self.postal_code}, {self.country}"
                )

            # German/Central European format
            elif country_code in {"DE", "AT", "CH", "NL", "BE", "LU", "CZ", "SK", "PL", "HU"}:
                self._cached_formatted_address = (
                    f"{self.street} {self.house_number}, {self.postal_code} {self.city}, {self.country}"
                )

            # French format
            elif country_code == "FR":
                self._cached_formatted_address = (
                    f"{self.house_number} {self.street}, {self.postal_code} {self.city}, {self.country}"
                )

            # Spanish/Italian/Portuguese format
            elif country_code in {"ES", "IT", "PT", "BR", "VE"}:
                self._cached_formatted_address = (
                    f"{self.street}, {self.house_number}, {self.postal_code} {self.city}, {self.country}"
                )

            # Scandinavian format
            elif country_code in {"DK", "NO", "SE", "FI", "IS"}:
                self._cached_formatted_address = (
                    f"{self.street} {self.house_number}, {self.postal_code} {self.city}, {self.country}"
                )

            # Default international format for other countries
            else:
                self._cached_formatted_address = (
                    f"{self.house_number} {self.street}, {self.postal_code} {self.city}, {self.state}, {self.country}"
                )

        assert self._cached_formatted_address is not None  # Ensure non-None for type checker
        return self._cached_formatted_address

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
        """Get the area code."""
        city_entity = self._get_city_entity()
        city_row = self._get_city_row()
        area_code_idx = city_entity._city_header_dict.get("areaCode")
        if area_code_idx is not None:
            return city_row[area_code_idx]
        return ""

    def reset(self) -> None:
        """Reset all cached values and field generators."""
        # Reset all field generators
        for key in self._field_generator:
            self._field_generator[key].reset()

        # Reset cached values
        self._cached_formatted_address = None
        self._cached_latitude = None
        self._cached_longitude = None
        self._cached_continent = None
        self._cached_iata_code = None
        self._cached_icao_code = None
        self._cached_calling_code = None

        # Reset entity caches
        self._current_city_row = None
        self._current_city_entity = None

        # Reset entities
        self._city_entity.reset()
