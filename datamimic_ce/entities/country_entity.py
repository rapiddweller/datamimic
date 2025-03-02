# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import Any

from datamimic_ce.entities.entity_util import FieldGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class CountryEntity:
    """
    Represents a country entity with various attributes.

    This class provides methods to load and access country data from a CSV file.
    Country data includes ISO codes, names, languages, phone codes, and population.
    """

    # File path is constant for all instances
    _COUNTRY_FILE_PATH = Path(__file__).parent.parent.joinpath("data/common/country.csv")

    # Cache for country data to avoid reloading
    _country_data_cache: list[tuple[Any, ...]] = []

    # Country code to index mapping for faster lookups
    _country_code_index: dict[str, int] = {}

    def __init__(self, cls_factory_util: BaseClassFactoryUtil):
        """
        Initialize the CountryEntity.

        Args:
            cls_factory_util (BaseClassFactoryUtil): The class factory utility.
        """
        # Keep a reference to data for backward compatibility
        self._data = self._load_country_data()

        # Initialize field generator to randomly select a country
        self._row_gen = FieldGenerator(
            lambda: self._data[cls_factory_util.get_data_generation_util().rnd_int(0, len(self._data) - 1)]
        )

        # Track selected country for more efficient property access
        self._selected_country = None

    @classmethod
    def _load_country_data(cls) -> list[tuple[Any, ...]]:
        """
        Load country data from file if not already cached.

        Returns:
            List of country data tuples
        """
        if not cls._country_data_cache:
            cls._country_data_cache = FileUtil.read_csv_to_dict_of_tuples_without_header_and_fill_missing_value(
                cls._COUNTRY_FILE_PATH
            )

            # Build index for faster lookup by country code
            for i, country in enumerate(cls._country_data_cache):
                cls._country_code_index[country[0]] = i

        return cls._country_data_cache

    def _get_country_row(self) -> tuple[Any, ...] | None:
        """
        Get the selected country row.

        Returns:
            Tuple containing country data
        """
        if self._selected_country is None:
            self._selected_country = self._row_gen.get()
        return self._selected_country

    @classmethod
    def get_by_iso_code(cls, iso_code: str) -> tuple[Any, ...] | None:
        """
        Get country data by ISO code.

        Args:
            iso_code: The ISO code to look up

        Returns:
            Country data tuple or None if not found
        """
        # Ensure data is loaded
        cls._load_country_data()

        index = cls._country_code_index.get(iso_code)
        if index is not None:
            return cls._country_data_cache[index]
        return None

    @property
    def iso_code(self) -> str | None:
        """
        Get the ISO code of the country.

        Returns:
            str: The ISO code of the country.
        """
        country_row = self._get_country_row()
        return country_row[0] if country_row else None

    @property
    def name(self) -> str | None:
        """
        Get the name of the country.

        Returns:
            str: The name of the country.
        """
        country_row = self._get_country_row()
        return country_row[4] if country_row else None

    @property
    def default_language_locale(self) -> str | None:
        """
        Get the default language locale of the country.

        Returns:
            str: The default language locale of the country.
        """
        country_row = self._get_country_row()
        return country_row[1] if country_row else None

    @property
    def phone_code(self) -> str | None:
        """
        Get the phone code of the country.

        Returns:
            str: The phone code of the country.
        """
        country_row = self._get_country_row()
        return country_row[2] if country_row else None

    @property
    def population(self) -> int | None:
        """
        Get the population of the country.

        Returns:
            int: The population of the country.
        """
        country_row = self._get_country_row()
        return int(country_row[5]) if country_row else None

    def reset(self) -> None:
        """
        Reset the field generator.

        This method resets the field generator to its initial state.
        """
        self._row_gen.reset()
        self._selected_country = None
