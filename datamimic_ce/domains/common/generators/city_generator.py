# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from typing import Any, ClassVar
from datamimic_ce.logger import logger
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class CityGenerator(BaseDomainGenerator):
    """Generator for city data.

    This class generates random city data using the CityDataLoader.
    """
    _DEFAULT_DATASET = "US"
    _city_data_dataset_not_found_set: ClassVar[set[str]] = set()
    _state_data_dataset_not_found_set: ClassVar[set[str]] = set()

    def __init__(self, country_code: str = "US"):
        """Initialize the CityGenerator.

        Args:
            country_code: The country code to use for generating cities.
        """
        super().__init__()
        self._country_code = country_code.upper()
        self._processed_city_data_dataset = None
        self._processed_state_data_dataset = None
    
    def _get_processed_dataset_list(self, dataset_not_found_list: set[str]) -> list[str]:
        """Get the processed dataset list.

        Args:
            dataset_not_found_list: The list of dataset not found.
        """
        processed_dataset_list = []
        if self._country_code not in dataset_not_found_list:
            processed_dataset_list.append(self._country_code)
        for fallback_country_code in self._REGIONAL_FALLBACKS.get(self._country_code, ()):
            if fallback_country_code not in processed_dataset_list and fallback_country_code not in dataset_not_found_list:
                processed_dataset_list.append(fallback_country_code)
        if self._DEFAULT_DATASET not in processed_dataset_list and self._DEFAULT_DATASET not in dataset_not_found_list:
            processed_dataset_list.append(self._DEFAULT_DATASET)
        return processed_dataset_list

    def _load_city_data(self) -> tuple[dict[str, int], list[tuple]]:
        """Load city data from CSV file.

        Returns:
            A tuple containing the header dictionary and city data.
        """
        if self._processed_city_data_dataset is None:
            processed_dataset_list = self._get_processed_dataset_list(self._city_data_dataset_not_found_set)
            
            for dataset in processed_dataset_list:
                try:
                    file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "city" / f"city_{dataset}.csv"
                    return_value = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path), read_func=lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=";"))
                    self._processed_city_data_dataset = dataset
                    return return_value
                except FileNotFoundError as e:
                    self._city_data_dataset_not_found_set.add(dataset)  
                    logger.warning(f"Error loading dataset '{dataset}': {e}")
            
            raise ValueError(f"No city data found for '{self._country_code}'")
                    
        else:
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "city" / f"city_{self._processed_city_data_dataset}.csv"
            return FileContentStorage.load_file_with_cache(str(file_path))
        
    def _load_country_name(self) -> str:
        """Load country name from CSV file.

        Returns:
            The name of the country.
        """
        cache_key = "country_name_dict"
        if cache_key in self._LOADED_DATA_CACHE:
            country_name_dict = self._LOADED_DATA_CACHE[cache_key]
        else:
            logger.debug("CACHE MISS: Loading country name data from file")
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "common" / "country.csv"
            country_df = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path), read_func=lambda: FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=","))
            country_name_dict = {row[0]: row[3] for row in country_df}
            self._LOADED_DATA_CACHE[cache_key] = country_name_dict
        return country_name_dict[self._country_code]

    def get_random_city(self) -> dict[str, Any]:
        """Get a random city.

        Returns:
            A dictionary containing the city data.
        """
        import random

        # Load city data
        city_header_dict, city_data = self._load_city_data()

        # Get random index
        random_index = random.randint(0, len(city_data) - 1)

        # Get city row
        city_row = city_data[random_index]

        # Load state data
        # state_dict = self._load_state_data()

        # Load country name
        country_name = self._load_country_name()

        # Build city dictionary
        return {
            "name": city_row[city_header_dict.get("name")],
            "postal_code": city_row[city_header_dict.get("postalCode")],
            "area_code": city_row[city_header_dict.get("areaCode")],
            "state_id": city_row[city_header_dict.get("state.id")] if "state.id" in city_header_dict else None,
            "state": city_row[city_header_dict.get("state")] if "state" in city_header_dict else None,
            "language": city_row[city_header_dict.get("language")] if "language" in city_header_dict else None,
            "population": city_row[city_header_dict.get("population")] if "population" in city_header_dict else None,
            "name_extension": city_row[city_header_dict.get("nameExtension")] if "nameExtension" in city_header_dict else "",
            "country": country_name,
            "country_code": self._country_code,
        }
