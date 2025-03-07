# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# """
# Base data loader for all entity data loaders.

# This module provides a base class for loading data from CSV files for various entities.
# """

# from abc import ABC, abstractmethod
# import csv
# from pathlib import Path
# from typing import ClassVar

# from datamimic_ce.logger import logger
# from datamimic_ce.utils.data_path_util import DataPathUtil


from abc import ABC
from pathlib import Path
from typing import Any, ClassVar
from venv import logger

from datamimic_ce.utils.file_util import FileUtil


class BaseDataLoader(ABC):
    # IMPORTANT: This cache is use for modified loaded data only, because file data is cached in FileContentStorage
    # For example, after loading data from file, you only want to use some columns of the data, 
    # you can use this cache to store these portions of data
    _LOADED_DATA_CACHE: ClassVar[dict[str, Any]] = {}

    # Regional fallbacks for countries
    _REGIONAL_FALLBACKS: dict[str, tuple[str, ...]] = {
        # Western Europe fallbacks
        "DE": ("AT", "CH", "LU"),  # German-speaking
        "FR": ("BE", "CH", "LU", "MC"),  # French-speaking
        "IT": ("CH", "SM", "VA"),  # Italian-speaking
        "NL": ("BE", "LU"),  # Dutch-speaking
        # Nordic fallbacks
        "SE": ("NO", "DK", "FI"),  # Scandinavian
        "NO": ("SE", "DK", "FI"),
        "DK": ("NO", "SE", "DE"),
        "FI": ("SE", "EE"),
        # Eastern Europe fallbacks
        "PL": ("CZ", "SK", "DE"),
        "CZ": ("SK", "PL", "AT"),
        "SK": ("CZ", "PL", "HU"),
        "HU": ("SK", "RO", "AT"),
        # Balkan fallbacks
        "BA": ("HR", "RS", "SI"),  # Bosnia fallbacks
        "HR": ("SI", "BA", "AT"),
        "RS": ("BA", "BG", "RO"),
        # English-speaking fallbacks
        "US": ("CA", "GB", "AU"),
        "GB": ("IE", "US", "CA"),
        "CA": ("US", "GB"),
        "AU": ("NZ", "GB", "US"),
        "NZ": ("AU", "GB", "US"),
    }

    # def _load_data_from_cache_or_file_with_header(cls, cache_key: str, file_path_str: str):
    #     try:
    #         if country_code in cls._LOADED_DATA_CACHE[cache_key]:
    #             return cls._LOADED_DATA_CACHE[cache_key][country_code]
    #         else:
    #             logger.debug("Dataloader cache miss, loading data from file")
    #             file_path = Path(__file__).parent / "data" / file_path_str / f"{country_code}.csv"
    #             header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=";")
    #             cls._LOADED_DATA_CACHE[cache_key][country_code] = (header_dict, data)
    #             return header_dict, data
    #     except FileNotFoundError as e:
    #         raise e
        
    # def _load_data_from_cache_or_file_with_header(cls, cache_dict: dict, country_code: str, file_path_str: str):
    #     try:
    #         if country_code in cache_dict:
    #             return cache_dict[country_code]
    #         else:
    #             logger.debug("Dataloader cache miss, loading data from file")
    #             file_path = Path(__file__).parent / "data" / file_path_str / f"{country_code}.csv"
    #             data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=";")
    #             cache_dict[country_code] = data
    #             return data
    #     except FileNotFoundError as e:
    #         raise e

    # def load_csv_data_by_country_domain(cls, country_code: str, relative_path: str):
    #     # Try to load data from file
    #     file_path = Path(__file__).parent / "data" / relative_path / f"{country_code}.csv"
    #     if not file_path.exists():
    #         logger.warning(f"CSV file not found: {file_path}")
    #         raise FileNotFoundError(f"CSV file not found: {file_path}")

    #     header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=";")

    #     return header_dict, data


    # @classmethod
    # def get_country_specific_data(
    #     cls,
    #     data_type: str,
    #     country_code: str = "US",
    #     domain_path: str = "",
    # ) -> list[tuple[str, float]]:
    #     """Get country-specific data for a specific type.

    #     Args:
    #         data_type: The type of data to retrieve
    #         country_code: The country code to use
    #         domain_path: The domain path to use

    #     Returns:
    #         A list of tuples containing values and weights
    #     """
    #     # Get the cache dictionary for the data type
    #     cache_dict = cls._get_cache_for_data_type(data_type)

    #     # Check if the data is already in the cache
    #     cache_key = f"{country_code}_{data_type}"
    #     if cache_key in cache_dict:
    #         return cache_dict[cache_key]

    #     # Try to load country-specific data from the country-specific file
    #     country_path = DataPathUtil.get_data_file_path(f"{domain_path}/{data_type}/{country_code}_{data_type}.csv")
    #     if country_path.exists():
    #         data = cls._load_simple_csv(country_path)
    #         if data:
    #             cache_dict[cache_key] = data
    #             return data

    #     # Try to load generic data
    #     generic_path = DataPathUtil.get_data_file_path(f"{domain_path}/{data_type}/{data_type}.csv")
    #     if generic_path.exists():
    #         data = cls._load_simple_csv(generic_path)
    #         if data:
    #             cache_dict[cache_key] = data
    #             return data

    #     # Use default values if no data files are available
    #     default_values = cls._get_default_values(data_type)
    #     cache_dict[cache_key] = default_values
    #     return default_values

    # @classmethod
    # @abstractmethod
    # def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
    #     """Get the appropriate cache dictionary for a data type.

    #     Args:
    #         data_type: The type of data

    #     Returns:
    #         A cache dictionary for the data type
    #     """
    #     # This method should be overridden by subclasses to return the appropriate cache
    #     raise NotImplementedError(f"Subclasses must implement function _get_cache_for_data_type()")

