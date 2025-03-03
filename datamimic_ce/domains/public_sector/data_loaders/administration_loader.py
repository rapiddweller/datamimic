# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration data loader.

This module provides data loading functionality for administration-related data,
loading reference data from CSV files for government agencies and positions.
"""

from typing import Any, ClassVar

from datamimic_ce.domains.public_sector.data_loaders.public_sector_loader import PublicSectorDataLoader


class AdministrationDataLoader(PublicSectorDataLoader):
    """Data loader for administration related data.

    This class loads administration information from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _AGENCIES_CACHE: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _AGENCIES_BY_WEIGHT_CACHE: ClassVar[dict[str, list[tuple[dict[str, Any], float]]]] = {}
    _POSITIONS_CACHE: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _POSITIONS_BY_WEIGHT_CACHE: ClassVar[dict[str, list[tuple[dict[str, Any], float]]]] = {}

    @classmethod
    def load_agencies(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Load government agency data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of government agency dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._AGENCIES_CACHE:
            return cls._AGENCIES_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/administration", "agencies", dataset)

        # Load the data
        agencies = cls._load_data(file_path)

        # Cache the data
        cls._AGENCIES_CACHE[dataset_key] = agencies

        # Also load with weights
        cls._load_agencies_by_weight(dataset)

        return agencies

    @classmethod
    def _load_agencies_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Load government agency data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing government agency dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._AGENCIES_BY_WEIGHT_CACHE:
            return cls._AGENCIES_BY_WEIGHT_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/administration", "agencies", dataset)

        # Load the data with weights
        agencies_by_weight = cls._load_data_with_weight(file_path)

        # Cache the data
        cls._AGENCIES_BY_WEIGHT_CACHE[dataset_key] = agencies_by_weight

        return agencies_by_weight

    @classmethod
    def load_positions(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Load administrative position data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of administrative position dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._POSITIONS_CACHE:
            return cls._POSITIONS_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/administration", "positions", dataset)

        # Load the data
        positions = cls._load_data(file_path)

        # Cache the data
        cls._POSITIONS_CACHE[dataset_key] = positions

        # Also load with weights
        cls._load_positions_by_weight(dataset)

        return positions

    @classmethod
    def _load_positions_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Load administrative position data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing administrative position dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._POSITIONS_BY_WEIGHT_CACHE:
            return cls._POSITIONS_BY_WEIGHT_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path("public_sector/administration", "positions", dataset)

        # Load the data with weights
        positions_by_weight = cls._load_data_with_weight(file_path)

        # Cache the data
        cls._POSITIONS_BY_WEIGHT_CACHE[dataset_key] = positions_by_weight

        return positions_by_weight
