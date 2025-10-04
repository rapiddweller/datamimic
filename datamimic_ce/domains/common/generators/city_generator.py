# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random as _random
from pathlib import Path
from typing import Any

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class CityGenerator(BaseDomainGenerator):
    """Generator for city data.

    This class generates random city data from the dataset.
    """

    def __init__(self, dataset: str | None = None, rng: _random.Random | None = None):
        """Initialize the CityGenerator.

        Args:
            dataset: The dataset to use for generating cities.
        """
        self._dataset = (dataset or "US").upper()  #  normalize dataset once for consistent file lookups
        self._rng: _random.Random = rng or _random.Random()
        self._country_name = None
        self._city_data = None
        self._last_state: str | None = None

    def _get_city_data(self):
        """Load city data from CSV file.

        Returns:
            A tuple containing the header dictionary and city data.
        """
        if self._city_data is None:
            #  use unified dataset path resolver and normalize error type for unsupported datasets
            try:
                file_path = dataset_path("common", "city", f"city_{self._dataset}.csv", start=Path(__file__))
                self._city_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=";")
            except FileNotFoundError as e:
                raise ValueError(f"Unsupported dataset for city data: {self._dataset}") from e
        return self._city_data

    def _get_country_name(self):
        """Get country name from CSV file.

        Returns:
            The name of the country.
        """
        if self._country_name is None:
            try:
                file_path = dataset_path("common", f"country_{self._dataset}.csv", start=Path(__file__))
                country_df = FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=",")
                country_name_dict = {row[0]: row[4] for row in country_df}
                self._country_name = country_name_dict.get(self._dataset) or country_name_dict.get("US")
                if not self._country_name:
                    raise ValueError(f"Country name not found for dataset {self._dataset} and US fallback unavailable")
            except (FileNotFoundError, ValueError, IndexError, KeyError) as e:
                raise ValueError(f"Unable to resolve country name for dataset {self._dataset}") from e
        return self._country_name

    def get_random_city(self) -> dict[str, Any]:
        """Get a random city.

        Returns:
            A dictionary containing the city data.
        """
        # Load city data
        city_header_dict, city_data = self._get_city_data()

        # Choose a row, avoiding immediate state repetition when possible
        if self._last_state is not None and len(city_data) > 1:
            # try up to 5 times to find different state
            attempt = 0
            city_row = None
            state_idx = city_header_dict.get("state.id")
            while attempt < 5:
                random_index = self._rng.randint(0, len(city_data) - 1)
                candidate = city_data[random_index]
                cand_state = candidate[state_idx] if state_idx is not None else None
                if cand_state != self._last_state:
                    city_row = candidate
                    break
                attempt += 1
            if city_row is None:
                city_row = city_data[self._rng.randint(0, len(city_data) - 1)]
        else:
            random_index = self._rng.randint(0, len(city_data) - 1)
            city_row = city_data[random_index]

        # Load state data
        # state_dict = self._load_state_data()

        # Load country name
        country_name = self._get_country_name()

        # Build city dictionary
        idx_name = city_header_dict.get("name")
        idx_postal = city_header_dict.get("postalCode")
        idx_area = city_header_dict.get("areaCode")
        idx_state = city_header_dict.get("state.id") if "state.id" in city_header_dict else None
        idx_lang = city_header_dict.get("language") if "language" in city_header_dict else None
        idx_pop = city_header_dict.get("population") if "population" in city_header_dict else None
        idx_ext = city_header_dict.get("nameExtension") if "nameExtension" in city_header_dict else None
        assert idx_name is not None and idx_postal is not None and idx_area is not None
        result = {
            "name": city_row[idx_name],
            "postal_code": city_row[idx_postal],
            "area_code": city_row[idx_area],
            "state": (city_row[idx_state] if idx_state is not None else None),
            "language": (city_row[idx_lang] if idx_lang is not None else None),
            "population": (city_row[idx_pop] if idx_pop is not None else None),
            "name_extension": (city_row[idx_ext] if idx_ext is not None else ""),
            "country": country_name,
            "country_code": self._dataset,
        }
        # remember last state for anti-repetition
        self._last_state = result.get("state")
        return result
