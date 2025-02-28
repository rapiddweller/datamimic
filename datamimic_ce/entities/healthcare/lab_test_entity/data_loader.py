# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Data loader for lab test entity.

This module provides functionality for loading data from CSV files for lab test entities.
"""

import csv
from pathlib import Path

from datamimic_ce.logger import logger
from datamimic_ce.utils.data_path_util import DataPathUtil


class LabTestDataLoader:
    """Data loader for lab test entity data."""

    # Module-level cache for data to reduce file I/O
    _DATA_CACHE: dict[str, list[tuple[str, float]]] = {}

    # Module-level cache for component data
    _COMPONENT_CACHE: dict[str, list[dict[str, str]]] = {}

    # Module-level cache for dictionary data
    _DICT_CACHE: dict[str, dict[str, str]] = {}

    # Specific caches for different data types
    _TEST_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _LAB_NAMES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _TEST_STATUSES_CACHE: dict[str, list[tuple[str, float]]] = {}
    _ABNORMAL_FLAGS_CACHE: dict[str, list[tuple[str, float]]] = {}
    _SPECIMEN_TYPES_CACHE: dict[str, list[tuple[str, float]]] = {}

    @classmethod
    def _load_simple_csv(cls, file_path: Path) -> list[tuple[str, float]]:
        """Load a simple CSV file and return a list of values with weights.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of tuples containing (value, weight)
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
    def get_country_specific_data(cls, data_type: str, country_code: str = "US") -> list[tuple[str, float]]:
        """Get country-specific data from CSV files.

        Args:
            data_type: The type of data to get (e.g., "test_types", "lab_names")
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A list of tuples containing (value, weight)
        """
        # Get the appropriate cache for the data type
        cache = cls._get_cache_for_data_type(data_type)
        cache_key = f"{data_type}_{country_code}"

        # Check if the data is already in the cache
        if cache_key in cache:
            return cache[cache_key]

        # Get the file path for the country-specific data
        file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, country_code)

        # Load the data from the CSV file
        data = cls._load_simple_csv(file_path)

        # If no data was found, try to load the default (US) data
        if not data and country_code != "US":
            file_path = DataPathUtil.get_country_specific_data_file_path("medical", data_type, "US")
            data = cls._load_simple_csv(file_path)

        # If still no data, use default values
        if not data:
            data = cls._get_default_values(data_type)

        # Cache the data for future use
        cache[cache_key] = data
        return data

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> dict[str, list[tuple[str, float]]]:
        """Get the appropriate cache dictionary for a data type.

        Args:
            data_type: The type of data

        Returns:
            The cache dictionary for the data type
        """
        if data_type == "test_types":
            return cls._TEST_TYPES_CACHE
        elif data_type == "lab_names":
            return cls._LAB_NAMES_CACHE
        elif data_type == "test_statuses":
            return cls._TEST_STATUSES_CACHE
        elif data_type == "abnormal_flags":
            return cls._ABNORMAL_FLAGS_CACHE
        elif data_type == "specimen_types":
            return cls._SPECIMEN_TYPES_CACHE
        else:
            # For unknown data types, create a new cache entry
            logger.warning(f"Unknown data type: {data_type}, creating new cache entry")
            setattr(cls, f"_{data_type.upper()}_CACHE", {})
            return getattr(cls, f"_{data_type.upper()}_CACHE")

    @classmethod
    def _get_default_values(cls, data_type: str) -> list[tuple[str, float]]:
        """Get default values for a data type when no file is found.

        Args:
            data_type: The type of data

        Returns:
            A list of default values with weights
        """
        if data_type == "test_types":
            return [
                ("Complete Blood Count", 10),
                ("Basic Metabolic Panel", 8),
                ("Comprehensive Metabolic Panel", 8),
                ("Lipid Panel", 7),
                ("Liver Function Tests", 6),
                ("Thyroid Function Tests", 6),
                ("Hemoglobin A1C", 5),
                ("Urinalysis", 5),
                ("Coagulation Panel", 4),
                ("Vitamin D", 3),
            ]
        elif data_type == "lab_names":
            return [
                ("Quest Diagnostics", 10),
                ("LabCorp", 10),
                ("Mayo Clinic Laboratories", 8),
                ("ARUP Laboratories", 7),
                ("BioReference Laboratories", 6),
                ("Sonic Healthcare", 5),
                ("Cleveland Clinic Laboratories", 5),
                ("Myriad Genetics", 4),
                ("Exact Sciences", 3),
                ("Guardant Health", 2),
            ]
        elif data_type == "test_statuses":
            return [
                ("Completed", 10),
                ("Pending", 5),
                ("In Progress", 5),
                ("Canceled", 2),
                ("Rejected", 1),
            ]
        elif data_type == "abnormal_flags":
            return [
                ("Normal", 10),
                ("High", 5),
                ("Low", 5),
                ("Critical High", 2),
                ("Critical Low", 2),
            ]
        elif data_type == "specimen_types":
            return [
                ("Blood", 10),
                ("Serum", 8),
                ("Plasma", 8),
                ("Urine", 7),
                ("Cerebrospinal Fluid", 3),
                ("Sputum", 3),
                ("Stool", 3),
                ("Tissue", 2),
                ("Swab", 2),
                ("Bone Marrow", 1),
            ]
        else:
            logger.warning(f"No default values for data type: {data_type}")
            return []

    @classmethod
    def get_test_component_mapping(cls, country_code: str = "US") -> dict[str, str]:
        """Get the mapping of test types to component files.

        Args:
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A dictionary mapping test types to component file names
        """
        # Create a cache key that includes the country code
        cache_key = f"test_components_mapping_{country_code}"

        # Check if the mapping is already in the cache
        if cache_key not in cls._DICT_CACHE:
            # If not, load it from the CSV file using DataPathUtil
            file_path = DataPathUtil.get_country_specific_data_file_path("medical", "test_components", country_code)

            if DataPathUtil.file_exists(file_path):
                # Load the mapping from the CSV file
                component_mapping: dict[str, str] = {}
                with open(file_path, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            test_type = row[0]
                            component_file = row[1]
                            component_mapping[test_type] = component_file
                # Store the mapping in the dictionary cache
                cls._DICT_CACHE[cache_key] = component_mapping
            else:
                # If the file doesn't exist and country code is not US, try US
                if country_code != "US":
                    file_path = DataPathUtil.get_country_specific_data_file_path("medical", "test_components", "US")
                    if DataPathUtil.file_exists(file_path):
                        us_mapping: dict[str, str] = {}
                        with open(file_path, encoding="utf-8") as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if len(row) >= 2:
                                    test_type = row[0]
                                    component_file = row[1]
                                    us_mapping[test_type] = component_file
                        cls._DICT_CACHE[cache_key] = us_mapping
                    else:
                        cls._DICT_CACHE[cache_key] = {}
                else:
                    # If the file doesn't exist, return an empty dictionary
                    cls._DICT_CACHE[cache_key] = {}

        return cls._DICT_CACHE[cache_key]

    @classmethod
    def get_test_components(cls, test_type: str, country_code: str = "US") -> list[dict[str, str]]:
        """Get the components for a specific test type.

        Args:
            test_type: The test type to get components for
            country_code: The country code to use (e.g., "US", "DE")

        Returns:
            A list of component dictionaries
        """
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
            components_dir = DataPathUtil.get_subdirectory_path("medical", "components")
            file_path = components_dir / component_file

            if DataPathUtil.file_exists(file_path):
                # Load the components from the CSV file
                components = []
                with open(file_path, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 3:
                            component = {"component": row[0], "unit": row[1], "reference_range": row[2]}
                            components.append(component)
                cls._COMPONENT_CACHE[cache_key] = components
            else:
                # If the file doesn't exist, try with US country code
                if country_code != "US":
                    us_component_file = component_file.replace(f"_{country_code}.csv", "_US.csv")
                    us_file_path = components_dir / us_component_file
                    if DataPathUtil.file_exists(us_file_path):
                        components = []
                        with open(us_file_path, encoding="utf-8") as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if len(row) >= 3:
                                    component = {"component": row[0], "unit": row[1], "reference_range": row[2]}
                                    components.append(component)
                        cls._COMPONENT_CACHE[cache_key] = components
                    else:
                        cls._COMPONENT_CACHE[cache_key] = cls._get_default_components()
                else:
                    # If the file doesn't exist, return default components
                    cls._COMPONENT_CACHE[cache_key] = cls._get_default_components()

        return cls._COMPONENT_CACHE[cache_key]

    @classmethod
    def _get_default_components(cls) -> list[dict[str, str]]:
        """Get default components when no component file is found.

        Returns:
            A list of default component dictionaries
        """
        return [
            {"component": "Hemoglobin", "unit": "g/dL", "reference_range": "13.5-17.5"},
            {"component": "Hematocrit", "unit": "%", "reference_range": "41-53"},
            {"component": "White Blood Cell Count", "unit": "K/uL", "reference_range": "4.5-11.0"},
            {"component": "Platelet Count", "unit": "K/uL", "reference_range": "150-450"},
            {"component": "Red Blood Cell Count", "unit": "M/uL", "reference_range": "4.5-5.9"},
        ]
