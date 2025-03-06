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
from typing import Any, ClassVar


class BaseDataLoader(ABC):
    _LOADED_DATA_CACHE: ClassVar[dict[str, Any]] = {}
#     """Base class for loading data from CSV files for all entities."""

#     # Subclasses should define their own caches with this pattern

#     @staticmethod
#     def _load_simple_csv(file_path: Path) -> list[tuple[str, float]]:
#         """Load a simple CSV file and return a list of values with weights.

#         Args:
#             file_path: Path to the CSV file

#         Returns:
#             List of tuples containing values and weights
#         """
#         if not file_path.exists():
#             logger.warning(f"CSV file not found: {file_path}")
#             return []

#         try:
#             with open(file_path, encoding="utf-8") as f:
#                 reader = csv.reader(f)
#                 values = []
#                 for row in reader:
#                     if not row:
#                         continue
#                     if len(row) >= 2:
#                         try:
#                             weight = float(row[1])
#                             values.append((row[0], weight))
#                         except ValueError:
#                             # Skip rows with non-numeric weights
#                             logger.warning(f"Skipping row with non-numeric weight: {row}")
#                     else:
#                         # If only one column, use default weight of 1.0
#                         values.append((row[0], 1.0))
#                 return values
#         except Exception as e:
#             logger.error(f"Error loading CSV file {file_path}: {e}")
#             return []

#     @classmethod
#     def get_country_specific_data(
#         cls,
#         data_type: str,
#         country_code: str = "US",
#         domain_path: str = "",
#     ) -> list[tuple[str, float]]:
#         """Get country-specific data for a specific type.

#         Args:
#             data_type: The type of data to retrieve
#             country_code: The country code to use
#             domain_path: The domain path to use

#         Returns:
#             A list of tuples containing values and weights
#         """
#         # Get the cache dictionary for the data type
#         cache_dict = cls._get_cache_for_data_type(data_type)

#         # Check if the data is already in the cache
#         cache_key = f"{country_code}_{data_type}"
#         if cache_key in cache_dict:
#             return cache_dict[cache_key]

#         # Try to load country-specific data from the country-specific file
#         country_path = DataPathUtil.get_data_file_path(f"{domain_path}/{data_type}/{country_code}_{data_type}.csv")
#         if country_path.exists():
#             data = cls._load_simple_csv(country_path)
#             if data:
#                 cache_dict[cache_key] = data
#                 return data

#         # Try to load generic data
#         generic_path = DataPathUtil.get_data_file_path(f"{domain_path}/{data_type}/{data_type}.csv")
#         if generic_path.exists():
#             data = cls._load_simple_csv(generic_path)
#             if data:
#                 cache_dict[cache_key] = data
#                 return data

#         # Use default values if no data files are available
#         default_values = cls._get_default_values(data_type)
#         cache_dict[cache_key] = default_values
#         return default_values

#     @classmethod
#     @abstractmethod
#     def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
#         """Get the appropriate cache dictionary for a data type.

#         Args:
#             data_type: The type of data

#         Returns:
#             A cache dictionary for the data type
#         """
#         # This method should be overridden by subclasses to return the appropriate cache
#         pass

#     @classmethod
#     @abstractmethod
#     def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
#         """Get default values for a data type when no data files are available.

#         Args:
#             data_type: The type of data

#         Returns:
#             A list of tuples containing default values and weights
#         """
#         # This method should be overridden by subclasses to provide default values
#         pass

#     # TODO: remove dead code
#     # @staticmethod
#     # def _load_csv_with_header(file_path: Path) -> list[dict[str, str]]:
#     #     """Load a CSV file with header and return a list of dictionaries.

#     #     Args:
#     #         file_path: Path to the CSV file

#     #     Returns:
#     #         List of dictionaries containing the CSV data
#     #     """
#     #     if not file_path.exists():
#     #         logger.warning(f"CSV file not found: {file_path}")
#     #         return []

#     #     try:
#     #         with open(file_path, encoding="utf-8") as f:
#     #             reader = csv.DictReader(f)
#     #             return list(reader)
#     #     except Exception as e:
#     #         logger.error(f"Error loading CSV file {file_path}: {e}")
#     #         return []
