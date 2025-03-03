# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Education data loader.

This module provides data loading functionality for education-related data,
loading reference data from CSV files for schools and educational roles.
"""

from typing import Any, ClassVar

from datamimic_ce.domains.public_sector.data_loaders.public_sector_loader import PublicSectorDataLoader


class EducationDataLoader(PublicSectorDataLoader):
    """Data loader for education related data.

    This class loads education information from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _SCHOOLS_CACHE: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _SCHOOLS_BY_WEIGHT_CACHE: ClassVar[dict[str, list[tuple[dict[str, Any], float]]]] = {}
    _ROLES_CACHE: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _ROLES_BY_WEIGHT_CACHE: ClassVar[dict[str, list[tuple[dict[str, Any], float]]]] = {}

    @classmethod
    def load_schools(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Load school data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of school dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._SCHOOLS_CACHE:
            return cls._SCHOOLS_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/education", "schools", dataset)

        # Load the data
        schools = cls._load_data(file_path)

        # Cache the data
        cls._SCHOOLS_CACHE[dataset_key] = schools

        # Also load with weights
        cls._load_schools_by_weight(dataset)

        return schools

    @classmethod
    def _load_schools_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Load school data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing school dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._SCHOOLS_BY_WEIGHT_CACHE:
            return cls._SCHOOLS_BY_WEIGHT_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/education", "schools", dataset)

        # Load the data with weights
        schools_by_weight = cls._load_data_with_weight(file_path)

        # Cache the data
        cls._SCHOOLS_BY_WEIGHT_CACHE[dataset_key] = schools_by_weight

        return schools_by_weight

    @classmethod
    def load_roles(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Load educational role data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of educational role dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._ROLES_CACHE:
            return cls._ROLES_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/education", "roles", dataset)

        # Load the data
        roles = cls._load_data(file_path)

        # Cache the data
        cls._ROLES_CACHE[dataset_key] = roles

        # Also load with weights
        cls._load_roles_by_weight(dataset)

        return roles

    @classmethod
    def _load_roles_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Load educational role data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing educational role dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._ROLES_BY_WEIGHT_CACHE:
            return cls._ROLES_BY_WEIGHT_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/education", "roles", dataset)

        # Load the data with weights
        roles_by_weight = cls._load_data_with_weight(file_path)

        # Cache the data
        cls._ROLES_BY_WEIGHT_CACHE[dataset_key] = roles_by_weight

        return roles_by_weight
