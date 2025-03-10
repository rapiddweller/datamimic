# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product data loader.

This module provides data loading functionality for product-related data,
loading reference data from CSV files for categories, brands, etc.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, cast

from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class ProductDataLoader(BaseDataLoader):
    """Data loader for product related data.

    This class loads product categories, brands, conditions, and other product-related data
    from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _CATEGORIES_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _BRANDS_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _CONDITIONS_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _AVAILABILITY_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _CURRENCIES_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _ADJECTIVES_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _PRODUCT_NOUNS_CACHE: ClassVar[Dict[str, Dict[str, List[Tuple[str, float]]]]] = {}

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> Dict[str, Any]:
        """Get the appropriate cache dictionary for the data type.

        Args:
            data_type: The type of data to get the cache for

        Returns:
            A cache dictionary for the data type
        """
        cache_map = {
            "categories": cls._CATEGORIES_CACHE,
            "brands": cls._BRANDS_CACHE,
            "conditions": cls._CONDITIONS_CACHE,
            "availability": cls._AVAILABILITY_CACHE,
            "currencies": cls._CURRENCIES_CACHE,
            "adjectives": cls._ADJECTIVES_CACHE,
            "product_nouns": cls._PRODUCT_NOUNS_CACHE,
        }
        
        return cache_map.get(data_type, {})

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
            "categories": "product_categories",
            "brands": "product_brands",
            "conditions": "product_conditions",
            "availability": "product_availability",
            "currencies": "currencies",
            "adjectives": "product_adjectives",
        }
        
        # Handle regular data types
        if data_type in file_map:
            base_name = file_map[data_type]
            # Use country-specific file if dataset (country) is provided
            if dataset:
                return f"ecommerce/{base_name}_{dataset}.csv"
            else:
                # First try with 'US' as default dataset
                file_path = f"ecommerce/{base_name}_US.csv"
                data_file_path = DataPathUtil.get_data_file_path(file_path)
                if Path(data_file_path).exists():
                    return file_path
                # Fallback to generic file without country code
                return f"ecommerce/{base_name}.csv"
        
        # Special case for product nouns which are organized by category
        if data_type.startswith("product_nouns_"):
            category = data_type.replace("product_nouns_", "")
            # Use country-specific file if dataset (country) is provided
            if dataset:
                return f"ecommerce/product_nouns_{category.lower()}_{dataset}.csv"
            else:
                # First try with 'US' as default dataset
                file_path = f"ecommerce/product_nouns_{category.lower()}_US.csv"
                data_file_path = DataPathUtil.get_data_file_path(file_path)
                if Path(data_file_path).exists():
                    return file_path
                # Fallback to generic file without country code
                return f"ecommerce/product_nouns_{category.lower()}.csv"
        
        return ""

    @classmethod
    def load_data(cls, data_type: str, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Load data for the specified type and dataset.

        Args:
            data_type: The type of data to load
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing values and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"
        
        # Check if the data is already cached
        cache = cls._get_cache_for_data_type(data_type)
        if dataset_key in cache:
            return cast(List[Tuple[str, float]], cache[dataset_key])
        
        # Get the file path
        file_path = cls._get_file_path_for_data_type(data_type, dataset)
        
        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_values(data_type)
            if data_type not in ("product_nouns",):
                # Cache the default data for non-compound types
                cache[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_values(data_type)
                if data_type not in ("product_nouns",):
                    # Cache the default data for non-compound types
                    cache[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            data = cls._load_csv_data(data_file_path)
            
            # Cache the data
            if data_type not in ("product_nouns",):
                # Cache the data for non-compound types
                cache[dataset_key] = data
            
            return data
        
        except Exception as e:
            print(f"Error loading {data_type} data: {e}")
            default_data = cls._get_default_values(data_type)
            if data_type not in ("product_nouns",):
                # Cache the default data for non-compound types
                cache[dataset_key] = default_data
            return default_data

    @classmethod
    def _load_csv_data(cls, file_path: str) -> List[Tuple[str, float]]:
        """Load weighted data from a CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            A list of tuples containing values and weights
        """
        try:
            # Load the CSV file
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path)
            
            result = []
            
            # Process each row
            for row in data:
                # Get the value and weight columns
                value = None
                weight = 1.0
                
                # Find the first column that's not 'weight'
                for key in header_dict.keys():
                    if key.lower() != "weight":
                        value_idx = header_dict[key]
                        value = row[value_idx]
                        break
                
                # Get the weight if it exists
                if "weight" in header_dict:
                    weight_idx = header_dict["weight"]
                    try:
                        weight = float(row[weight_idx])
                    except (ValueError, TypeError):
                        weight = 1.0
                
                if value is not None:
                    result.append((value, weight))
            
            return result
        
        except Exception as e:
            print(f"Error loading CSV data from {file_path}: {e}")
            return []

    @classmethod
    def _get_default_values(cls, data_type: str) -> List[Tuple[str, float]]:
        """Get default values for the specified data type.

        Args:
            data_type: The type of data to get default values for

        Returns:
            A list of tuples containing default values and weights
        """
        defaults = {
            "categories": [
                ("ELECTRONICS", 1.0),
                ("CLOTHING", 1.0),
                ("HOME_GOODS", 1.0),
                ("BOOKS", 1.0),
                ("FOOD", 1.0),
            ],
            "brands": [
                ("ACME", 1.0),
                ("TechPro", 1.0),
                ("HomeStyle", 1.0),
                ("FashionForward", 1.0),
                ("BudgetBasics", 1.0),
            ],
            "conditions": [
                ("NEW", 0.8),
                ("USED", 0.1),
                ("REFURBISHED", 0.05),
                ("OPEN_BOX", 0.03),
                ("DAMAGED", 0.02),
            ],
            "availability": [
                ("IN_STOCK", 0.7),
                ("OUT_OF_STOCK", 0.15),
                ("BACK_ORDERED", 0.1),
                ("DISCONTINUED", 0.03),
                ("PRE_ORDER", 0.02),
            ],
            "currencies": [
                ("USD", 1.0),
                ("EUR", 0.8),
                ("GBP", 0.7),
                ("JPY", 0.6),
                ("CAD", 0.5),
            ],
            "adjectives": [
                ("Premium", 1.0),
                ("Deluxe", 0.9),
                ("Essential", 1.0),
                ("Classic", 0.9),
                ("Modern", 0.9),
            ],
            "product_nouns_electronics": [
                ("Smartphone", 1.0),
                ("Laptop", 1.0),
                ("Tablet", 0.9),
                ("Headphones", 0.9),
                ("TV", 0.8),
            ],
            "product_nouns_clothing": [
                ("Shirt", 1.0),
                ("Pants", 1.0),
                ("Dress", 0.9),
                ("Jacket", 0.9),
                ("Shoes", 1.0),
            ],
        }
        
        return defaults.get(data_type, [])

    @classmethod
    def get_product_categories(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product categories with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product categories and weights
        """
        return cls.load_data("categories", dataset)

    @classmethod
    def get_product_brands(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product brands with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product brands and weights
        """
        return cls.load_data("brands", dataset)

    @classmethod
    def get_product_conditions(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product conditions with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product conditions and weights
        """
        return cls.load_data("conditions", dataset)

    @classmethod
    def get_product_availability(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product availability statuses with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product availability statuses and weights
        """
        return cls.load_data("availability", dataset)

    @classmethod
    def get_currencies(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get currency codes with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing currency codes and weights
        """
        return cls.load_data("currencies", dataset)
    
    @classmethod
    def get_product_adjectives(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product adjectives with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product adjectives and weights
        """
        return cls.load_data("adjectives", dataset)
    
    @classmethod
    def get_product_nouns(cls, category: str, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get product nouns for a specific category with weights.

        Args:
            category: The product category
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing product nouns and weights
        """
        data_type = f"product_nouns_{category.lower()}"
        return cls.load_data(data_type, dataset)