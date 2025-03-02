# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Base data loader for all entity data loaders.

This module provides a base class for loading data from CSV files for various entities.
"""

import csv
from pathlib import Path
from typing import ClassVar

from datamimic_ce.logger import logger
from datamimic_ce.utils.data_path_util import DataPathUtil


class BaseDataLoader:
    """Base class for loading data from CSV files for all entities."""

    # Subclasses should define their own caches with this pattern
    _CACHES: ClassVar[dict[str, dict[str, list[tuple[str, float]]]]] = {}

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples containing values and weights
        """
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.reader(f)
                values = []
                for row in reader:
                    if not row:
                        continue
                    if len(row) >= 2:
                        try:
                            weight = float(row[1])
                            values.append((row[0], weight))
                        except (ValueError, IndexError):
                            # If weight is not a valid number, use default weight of 1.0
                            values.append((row[0], 1.0))
                    else:
                        # If no weight is provided, use default weight of 1.0
                        values.append((row[0], 1.0))
                return values
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []

    @classmethod
    def get_country_specific_data(
        cls,
        data_type: str,
        country_code: str = "US",
        domain_path: str = "",
        cache_dict: dict[str, list[tuple[str, float]]] | None = None,
    ) -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        Args:
            data_type: Type of data to retrieve (e.g., "phases", "statuses")
            country_code: Country code (default: "US")
            domain_path: The path to the domain data (e.g., "medical/clinical_trials")
            cache_dict: Cache dictionary to use (default: use subclass _get_cache_for_data_type)

        Returns:
            List of tuples containing values and weights
        """
        # Get the appropriate cache for the data type
        cache = cache_dict if cache_dict is not None else cls._get_cache_for_data_type(data_type)
        cache_key = f"{data_type}_{country_code}"

        # Check if the data is already cached
        if cache_key in cache:
            return cache[cache_key]

        # Determine the file path based on data type and country code
        file_path = DataPathUtil.get_country_specific_data_file_path(domain_path, data_type, country_code)

        # Load the data from the CSV file
        data = cls._load_simple_csv(file_path)

        # If no data was found, try to load the default (US) data
        if not data and country_code != "US":
            file_path = DataPathUtil.get_country_specific_data_file_path(domain_path, data_type, "US")
            data = cls._load_simple_csv(file_path)

        # If still no data, log an error - no fallback to default values
        if not data:
            logger.error(
                f"No data file found for {data_type} with country code {country_code}. Please create a data file."
            )
            # Return empty list instead of using default values
            data = []

        # Cache the data for future use
        cache[cache_key] = data
        return data

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache for the data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            The appropriate cache dictionary
        """
        # Subclasses should override this method to return their specific cache
        cache_name = f"_{data_type.upper()}_CACHE"

        # Check if the cache exists
        if not hasattr(cls, cache_name):
            # Create a new cache if it doesn't exist
            logger.warning(f"Cache not found for data type: {data_type}, creating new cache")
            setattr(cls, cache_name, {})

        return getattr(cls, cache_name)

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type.

        Args:
            data_type: Type of data to retrieve

        Returns:
            List of tuples containing default values and weights
        """
        # Log an error and return an empty list - no hardcoded fallbacks
        logger.error(f"No data file found for {data_type}. Please create a data file.")
        return []

    @staticmethod
    def _load_csv_with_header(file_path: Path) -> list[dict[str, str]]:
        """Load a CSV file with header into a list of dictionaries.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of dictionaries with column names as keys.
        """
        if not file_path.exists():
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {e}")
            return []
