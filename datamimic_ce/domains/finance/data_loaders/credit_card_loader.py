# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Credit card data loader.

This module provides data loading functionality for credit card related data,
loading reference data from CSV files for credit card types and other information.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, cast

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class CreditCardLoader(BaseDataLoader):
    """Data loader for credit card related data.

    This class loads credit card types and related information from CSV files
    and provides methods to access this data.
    """

    # Cache for loaded data
    _CARD_TYPES_CACHE: ClassVar[Dict[str, List[Dict[str, Any]]]] = {}
    _CARD_TYPES_BY_WEIGHT_CACHE: ClassVar[Dict[str, List[Tuple[Dict[str, Any], float]]]] = {}

    @classmethod
    def _get_file_path_for_data_type(cls, data_type: str, dataset: Optional[str] = None) -> str:
        """Get the file path for the specified data type.

        Args:
            data_type: The type of data to get the file path for
            dataset: Optional dataset code (country code)

        Returns:
            The file path for the data type
        """
        # Map of data types to their base file names
        file_map = {
            "card_types": "finance/credit_card/card_types",
        }
        
        # Handle regular data types
        if data_type in file_map:
            base_name = file_map[data_type]
            # Use country-specific file if dataset (country) is provided
            if dataset:
                return f"{base_name}_{dataset}.csv"
            else:
                # First try with 'US' as default dataset
                file_path = f"{base_name}_US.csv"
                data_file_path = DataPathUtil.get_data_file_path(file_path)
                if Path(data_file_path).exists():
                    return file_path
                # Fallback to generic file without country code
                return f"{base_name}.csv"
        
        return ""

    @classmethod
    def load_card_types(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load credit card type data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of card type dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._CARD_TYPES_CACHE:
            return cls._CARD_TYPES_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("card_types", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_card_types(dataset)
            cls._CARD_TYPES_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_card_types(dataset)
                cls._CARD_TYPES_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            result = []
            
            # Process each row
            for row in data:
                card_type = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        # Parse specific fields
                        if key == "prefix":
                            # Split prefix by | to get multiple prefixes
                            prefixes = row[idx].split("|")
                            card_type[key] = prefixes
                        elif key in ["length", "cvv_length"]:
                            # Parse numeric values
                            try:
                                card_type[key] = int(row[idx])
                            except (ValueError, TypeError):
                                card_type[key] = 16 if key == "length" else 3
                        else:
                            card_type[key] = row[idx]
                
                # Add the card type to the result
                result.append(card_type)
            
            # Cache the data
            cls._CARD_TYPES_CACHE[dataset_key] = result
            
            # Also load as weighted data
            cls._load_card_types_by_weight(dataset)
            
            return result
        
        except Exception as e:
            print(f"Error loading card type data: {e}")
            default_data = cls._get_default_card_types(dataset)
            cls._CARD_TYPES_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _load_card_types_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Load card type data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing card type dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        if dataset_key in cls._CARD_TYPES_BY_WEIGHT_CACHE:
            return cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key]
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type("card_types", dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_card_types_by_weight(dataset)
            cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_card_types_by_weight(dataset)
                cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                default_data = cls._get_default_card_types_by_weight(dataset)
                cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data
            
            weight_idx = header_dict["weight"]
            
            result = []
            
            # Process each row
            for row in data:
                card_type = {}
                
                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        # Parse specific fields
                        if key == "prefix":
                            # Split prefix by | to get multiple prefixes
                            prefixes = row[idx].split("|")
                            card_type[key] = prefixes
                        elif key in ["length", "cvv_length"]:
                            # Parse numeric values
                            try:
                                card_type[key] = int(row[idx])
                            except (ValueError, TypeError):
                                card_type[key] = 16 if key == "length" else 3
                        else:
                            card_type[key] = row[idx]
                
                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0
                
                # Add the card type and weight to the result
                result.append((card_type, weight))
            
            # Cache the data
            cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key] = result
            
            return result
        
        except Exception as e:
            print(f"Error loading card type data with weights: {e}")
            default_data = cls._get_default_card_types_by_weight(dataset)
            cls._CARD_TYPES_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _get_default_card_types(cls, dataset: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get default card type data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of card type dictionaries
        """
        if dataset == "DE":
            return [
                {"type": "VISA", "prefix": ["4"], "length": 16, "cvv_length": 3},
                {"type": "MASTERCARD", "prefix": ["5"], "length": 16, "cvv_length": 3},
                {"type": "AMEX", "prefix": ["34", "37"], "length": 15, "cvv_length": 4},
                {"type": "EUROCARD", "prefix": ["5"], "length": 16, "cvv_length": 3},
            ]
        else:  # Default to US
            return [
                {"type": "VISA", "prefix": ["4"], "length": 16, "cvv_length": 3},
                {"type": "MASTERCARD", "prefix": ["5"], "length": 16, "cvv_length": 3},
                {"type": "AMEX", "prefix": ["34", "37"], "length": 15, "cvv_length": 4},
                {"type": "DISCOVER", "prefix": ["6011"], "length": 16, "cvv_length": 3},
            ]

    @classmethod
    def _get_default_card_types_by_weight(cls, dataset: Optional[str] = None) -> List[Tuple[Dict[str, Any], float]]:
        """Get default card type data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing card type dictionaries and weights
        """
        if dataset == "DE":
            return [
                ({"type": "VISA", "prefix": ["4"], "length": 16, "cvv_length": 3}, 0.35),
                ({"type": "MASTERCARD", "prefix": ["5"], "length": 16, "cvv_length": 3}, 0.35),
                ({"type": "AMEX", "prefix": ["34", "37"], "length": 15, "cvv_length": 4}, 0.2),
                ({"type": "EUROCARD", "prefix": ["5"], "length": 16, "cvv_length": 3}, 0.1),
            ]
        else:  # Default to US
            return [
                ({"type": "VISA", "prefix": ["4"], "length": 16, "cvv_length": 3}, 0.4),
                ({"type": "MASTERCARD", "prefix": ["5"], "length": 16, "cvv_length": 3}, 0.3),
                ({"type": "AMEX", "prefix": ["34", "37"], "length": 15, "cvv_length": 4}, 0.2),
                ({"type": "DISCOVER", "prefix": ["6011"], "length": 16, "cvv_length": 3}, 0.1),
            ]