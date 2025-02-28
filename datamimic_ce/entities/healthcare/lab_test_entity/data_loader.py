# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.utils.data_path_util import DataPathUtil


class LabTestDataLoader:
    """Data loader for lab test entity data."""

    # Module-level cache for data to reduce file I/O
    _DATA_CACHE: dict[str, list[tuple[str, float]]] = {}

    # Module-level cache for component data
    _COMPONENT_CACHE: dict[str, list[dict[str, str]]] = {}

    # Module-level cache for dictionary data
    _DICT_CACHE: dict[str, dict[str, str]] = {}

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples containing (value, weight)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                result = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse the line to extract value and weight
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        try:
                            weight = float(parts[1])
                            result.append((parts[0], weight))
                        except ValueError:
                            # If weight is not a valid number, treat it as part of the value
                            result.append((line, 1.0))
                    else:
                        # If no weight is specified, use a default weight of 1
                        result.append((line, 1.0))
                return result
        except Exception:
            return []

    @classmethod
    def _parse_weighted_value(cls, value: str) -> tuple[str, float]:
        """Parse a weighted value from a CSV file.

        Format: "value,weight" or just "value" (default weight is 1)

        Args:
            value: The value to parse

        Returns:
            A tuple of (value, weight)
        """
        parts = value.split(",", 1)
        if len(parts) == 2:
            try:
                weight = float(parts[1])
                return parts[0], weight
            except ValueError:
                # If the weight is not a valid number, treat it as part of the value
                return value, 1.0
        return value, 1.0

    @classmethod
    def get_country_specific_data(cls, data_type: str, country_code: str | None = None) -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        Args:
            data_type: The type of data to get (e.g., "test_types", "lab_names")
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A list of tuples containing (value, weight)
        """
        # If no country code is provided, use a default
        if not country_code:
            country_code = "US"  # Default to US if no country code is provided

        # Create a cache key that includes the country code
        cache_key = f"{data_type}_{country_code}"

        # Check if the data is already in the cache
        if cache_key not in cls._DATA_CACHE:
            # If not, load it from the CSV file using DataPathUtil
            file_path = DataPathUtil.get_country_specific_data_file_path("healthcare", data_type, country_code)

            if DataPathUtil.file_exists(file_path):
                cls._DATA_CACHE[cache_key] = cls._load_simple_csv(file_path)
            else:
                # If the file doesn't exist, return an empty list
                cls._DATA_CACHE[cache_key] = []

        return cls._DATA_CACHE[cache_key]

    @classmethod
    def get_test_component_mapping(cls, country_code: str | None = None) -> dict[str, str]:
        """Get the mapping of test types to component files.

        Args:
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A dictionary mapping test types to component file names
        """
        # If no country code is provided, use a default
        if not country_code:
            country_code = "US"  # Default to US if no country code is provided

        # Create a cache key that includes the country code
        cache_key = f"test_components_mapping_{country_code}"

        # Check if the mapping is already in the cache
        if cache_key not in cls._DICT_CACHE:
            # If not, load it from the CSV file using DataPathUtil
            file_path = DataPathUtil.get_country_specific_data_file_path("healthcare", "test_components", country_code)

            if DataPathUtil.file_exists(file_path):
                # Load the mapping from the CSV file
                mapping: dict[str, str] = {}
                for line in cls._load_simple_csv(file_path):
                    parts = line.split(",", 2)
                    if len(parts) >= 2:
                        test_type = parts[0]
                        component_file = parts[1]
                        mapping[test_type] = component_file
                # Store the mapping in the dictionary cache
                cls._DICT_CACHE[cache_key] = mapping
            else:
                # If the file doesn't exist, return an empty dictionary
                cls._DICT_CACHE[cache_key] = {}

        return cls._DICT_CACHE[cache_key]

    @classmethod
    def get_test_components(cls, test_type: str, country_code: str | None = None) -> list[dict[str, str]]:
        """Get the components for a specific test type.

        Args:
            test_type: The test type to get components for
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A list of component dictionaries
        """
        # If no country code is provided, use a default
        if not country_code:
            country_code = "US"  # Default to US if no country code is provided

        # Get the mapping of test types to component files
        test_component_mapping = cls.get_test_component_mapping(country_code)

        # If the test type is not in the mapping, try to find a default
        component_file = test_component_mapping.get(test_type)
        if not component_file:
            # Try to find a default component file for the test type
            # For example, if the test type contains "Blood", use blood test components
            if "Blood" in test_type or "Blut" in test_type:
                component_file = f"blood_test_components_{country_code}.csv"
            elif "Urin" in test_type or "Urinalysis" in test_type:
                component_file = f"urinalysis_components_{country_code}.csv"
            else:
                # Default to blood test components if no match is found
                component_file = f"blood_test_components_{country_code}.csv"

        # Create a cache key for the components
        cache_key = f"components_{component_file}"

        # Check if the components are already in the cache
        if cache_key not in cls._COMPONENT_CACHE:
            # If not, load them from the CSV file using DataPathUtil
            components_dir = DataPathUtil.get_subdirectory_path("healthcare", "components")
            file_path = components_dir / component_file

            if DataPathUtil.file_exists(file_path):
                # Load the components from the CSV file
                components = []
                for line in cls._load_simple_csv(file_path):
                    parts = line.split(",", 3)
                    if len(parts) >= 3:
                        component = {"component": parts[0], "unit": parts[1], "reference_range": parts[2]}
                        components.append(component)
                cls._COMPONENT_CACHE[cache_key] = components
            else:
                # If the file doesn't exist, return an empty list
                cls._COMPONENT_CACHE[cache_key] = []

        return cls._COMPONENT_CACHE[cache_key]
