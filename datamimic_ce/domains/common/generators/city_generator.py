# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_util import FileUtil


class CityGenerator(BaseDomainGenerator):
    """Generator for city data.

    This class generates random city data from the dataset.
    """

    def __init__(self, dataset: str | None = None):
        """Initialize the CityGenerator.

        Args:
            dataset: The dataset to use for generating cities.
        """
        self._dataset = dataset or "US"
        self._country_name = None
        self._city_data = None

    def _get_city_data(self):
        """Load city data from CSV file.

        Returns:
            A tuple containing the header dictionary and city data.
        """
        if self._city_data is None:
            try:
                file_path = (
                    Path(__file__).parent.parent.parent.parent
                    / "domain_data"
                    / "common"
                    / "city"
                    / f"city_{self._dataset}.csv"
                )
                self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=";")
            except FileNotFoundError as e:
                raise ValueError(f"No city data found for '{self._dataset}': {e}") from e
        return self._city_data

    def _get_country_name(self):
        """Get country name from CSV file.

        Returns:
            The name of the country.
        """
        if self._country_name is None:
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "country.csv"
            country_df = FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=",")
            country_name_dict = {row[0]: row[4] for row in country_df}
            self._country_name = country_name_dict[self._dataset]
        return self._country_name

    def get_random_city(self) -> dict[str, Any]:
        """Get a random city.

        Returns:
            A dictionary containing the city data.
        """
        import random

        # Load city data
        city_header_dict, city_data = self._get_city_data()

        # Get random index
        random_index = random.randint(0, len(city_data) - 1)

        # Get city row
        city_row = city_data[random_index]

        # Load state data
        # state_dict = self._load_state_data()

        # Load country name
        country_name = self._get_country_name()

        # Build city dictionary
        return {
            "name": city_row[city_header_dict.get("name")],
            "postal_code": city_row[city_header_dict.get("postalCode")],
            "area_code": city_row[city_header_dict.get("areaCode")],
            "state": city_row[city_header_dict.get("state.id")] if "state.id" in city_header_dict else None,
            "language": city_row[city_header_dict.get("language")] if "language" in city_header_dict else None,
            "population": city_row[city_header_dict.get("population")] if "population" in city_header_dict else None,
            "name_extension": city_row[city_header_dict.get("nameExtension")]
            if "nameExtension" in city_header_dict
            else "",
            "country": country_name,
            "country_code": self._dataset,
        }
