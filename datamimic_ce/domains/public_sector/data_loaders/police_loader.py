# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police data loader.

This module provides data loading functionality for police-related data,
loading reference data from CSV files for police departments and ranks.
"""

from typing import Any, ClassVar, Dict, List, Optional, Tuple

from datamimic_ce.domains.public_sector.data_loaders.public_sector_loader import PublicSectorDataLoader


class PoliceDataLoader(PublicSectorDataLoader):
    """Data loader for police related data.

    This class loads police information from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _DEPARTMENTS_CACHE: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}
    _DEPARTMENTS_BY_WEIGHT_CACHE: ClassVar[Dict[str, List[Tuple[Dict[str, Any], float]]]] = {}
    _RANKS_CACHE: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}
    _RANKS_BY_WEIGHT_CACHE: ClassVar[Dict[str, List[Tuple[Dict[str, Any], float]]]] = {}
    
    @classmethod
    def load_departments(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load police department data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of police department dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._DEPARTMENTS_CACHE:
            return cls._DEPARTMENTS_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path("public_sector/police", "departments", dataset)
        
        # Load the data
        departments = cls._load_data(file_path)
        
        # Cache the data
        cls._DEPARTMENTS_CACHE[dataset_key] = departments
        
        # Also load with weights
        cls._load_departments_by_weight(dataset)
        
        return departments
    
    @classmethod
    def _load_departments_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load police department data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing police department dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._DEPARTMENTS_BY_WEIGHT_CACHE:
            return cls._DEPARTMENTS_BY_WEIGHT_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path("public_sector/police", "departments", dataset)
        
        # Load the data with weights
        departments_by_weight = cls._load_data_with_weight(file_path)
        
        # Cache the data
        cls._DEPARTMENTS_BY_WEIGHT_CACHE[dataset_key] = departments_by_weight
        
        return departments_by_weight
    
    @classmethod
    def load_ranks(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load police rank data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of police rank dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._RANKS_CACHE:
            return cls._RANKS_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path("public_sector/police", "ranks", dataset)
        
        # Load the data
        ranks = cls._load_data(file_path)
        
        # Cache the data
        cls._RANKS_CACHE[dataset_key] = ranks
        
        # Also load with weights
        cls._load_ranks_by_weight(dataset)
        
        return ranks
    
    @classmethod
    def _load_ranks_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load police rank data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing police rank dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._RANKS_BY_WEIGHT_CACHE:
            return cls._RANKS_BY_WEIGHT_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path("public_sector/police", "ranks", dataset)
        
        # Load the data with weights
        ranks_by_weight = cls._load_data_with_weight(file_path)
        
        # Cache the data
        cls._RANKS_BY_WEIGHT_CACHE[dataset_key] = ranks_by_weight
        
        return ranks_by_weight