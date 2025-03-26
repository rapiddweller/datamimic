# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class CountryGenerator(BaseDomainGenerator):
    """Generator for country-related attributes.

    Provides methods to generate country-related attributes such as
    ISO code, name, default language locale, phone code, and population.
    """

    def __init__(self):
        pass

    def load_country_data(self):
        """Load country data from CSV file.

        Returns:
            A dictionary containing country data.
        """
        # Prepare data file path
        country_file_path = self._get_base_path_country() / "country.csv"

        try:
            # Load country data
            country_data = FileUtil.read_csv_to_list_of_tuples_without_header(country_file_path, delimiter=",")

            country_data_dict = {country[0]: country for country in country_data}

            return country_data_dict

        except Exception as e:
            logger.error(f"Error loading country data: {e}")
            raise e

    def get_country_by_iso_code(self, iso_code: str):
        """Get a country by ISO code.

        Args:
            iso_code: The ISO code of the country to get.

        Returns:
            A dictionary containing the country data, or None if not found.
        """
        # Load country data
        country_data = self.load_country_data()

        return_value = country_data.get(iso_code)
        if return_value is None:
            raise ValueError(f"Country with ISO code {iso_code} not found")
        return return_value

    def get_random_country(self) -> dict[str, Any]:
        """Get a random country.

        Returns:
            A dictionary containing the country data.
        """
        import random

        # Load country data
        country_data = self.load_country_data()

        # Get random index
        random_index = random.randint(0, len(country_data) - 1)

        # Get country row
        country_row = list(country_data.values())[random_index]

        # Build country dictionary
        return {
            "iso_code": country_row[0],
            "default_language_locale": country_row[1],
            "phone_code": country_row[2],
            "name": country_row[4],
            "population": country_row[5],
        }

    def _get_base_path_country(self) -> Path:
        """Get the base path for country data.

        Returns:
            The base path for country data.
        """
        return Path(__file__).parent.parent.parent.parent / "domain_data" / "common"
