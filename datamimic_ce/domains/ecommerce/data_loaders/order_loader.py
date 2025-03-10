# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Order data loader.

This module provides data loading functionality for order-related data,
loading reference data from CSV files for order statuses, payment methods, etc.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, cast

from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class OrderDataLoader(BaseDataLoader):
    """Data loader for order related data.

    This class loads order statuses, payment methods, shipping methods, and other
    order-related data from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _ORDER_STATUSES_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _PAYMENT_METHODS_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _SHIPPING_METHODS_CACHE: ClassVar[Dict[str, List[Tuple[str, float]]]] = {}
    _SHIPPING_COSTS_CACHE: ClassVar[Dict[str, Dict[str, Tuple[float, float]]]] = {}

    @classmethod
    def _get_cache_for_data_type(cls, data_type: str) -> Dict[str, Any]:
        """Get the appropriate cache dictionary for the data type.

        Args:
            data_type: The type of data to get the cache for

        Returns:
            A cache dictionary for the data type
        """
        cache_map = {
            "order_statuses": cls._ORDER_STATUSES_CACHE,
            "payment_methods": cls._PAYMENT_METHODS_CACHE,
            "shipping_methods": cls._SHIPPING_METHODS_CACHE,
            "shipping_costs": cls._SHIPPING_COSTS_CACHE,
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
            "order_statuses": "order_statuses",
            "payment_methods": "payment_methods",
            "shipping_methods": "shipping_methods",
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
            cache[dataset_key] = default_data
            return default_data
        
        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_values(data_type)
                cache[dataset_key] = default_data
                return default_data
            
            # Load data from CSV
            data = cls._load_csv_data(data_file_path)
            
            # Cache the data
            cache[dataset_key] = data
            
            # If this is shipping methods, also load the shipping costs
            if data_type == "shipping_methods":
                cls._load_shipping_costs(data_file_path, dataset_key)
            
            return data
        
        except Exception as e:
            print(f"Error loading {data_type} data: {e}")
            default_data = cls._get_default_values(data_type)
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
                
                # Find the first column that's not 'weight' or related to costs
                for key in header_dict.keys():
                    if key.lower() not in ["weight", "min_cost", "max_cost"]:
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
    def _load_shipping_costs(cls, file_path: str, dataset_key: str) -> None:
        """Load shipping costs from a CSV file.

        Args:
            file_path: Path to the CSV file
            dataset_key: The dataset key for caching
        """
        try:
            # Load the CSV file
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path)
            
            # Skip if min_cost or max_cost columns don't exist
            if "min_cost" not in header_dict or "max_cost" not in header_dict:
                return
            
            # Get the method column index
            method_idx = None
            for key in header_dict.keys():
                if key.lower() not in ["weight", "min_cost", "max_cost"]:
                    method_idx = header_dict[key]
                    break
            
            if method_idx is None:
                return
            
            min_cost_idx = header_dict["min_cost"]
            max_cost_idx = header_dict["max_cost"]
            
            costs = {}
            
            # Process each row
            for row in data:
                method = row[method_idx]
                try:
                    min_cost = float(row[min_cost_idx])
                    max_cost = float(row[max_cost_idx])
                    costs[method] = (min_cost, max_cost)
                except (ValueError, TypeError):
                    costs[method] = (5.0, 15.0)  # Default values
            
            # Cache the costs
            cls._SHIPPING_COSTS_CACHE[dataset_key] = costs
        
        except Exception as e:
            print(f"Error loading shipping costs from {file_path}: {e}")

    @classmethod
    def _get_default_values(cls, data_type: str) -> List[Tuple[str, float]]:
        """Get default values for the specified data type.

        Args:
            data_type: The type of data to get default values for

        Returns:
            A list of tuples containing default values and weights
        """
        defaults = {
            "order_statuses": [
                ("PENDING", 0.1),
                ("PROCESSING", 0.15),
                ("SHIPPED", 0.15),
                ("DELIVERED", 0.3),
                ("CANCELLED", 0.05),
                ("COMPLETED", 0.25),
            ],
            "payment_methods": [
                ("CREDIT_CARD", 0.4),
                ("DEBIT_CARD", 0.3),
                ("PAYPAL", 0.15),
                ("BANK_TRANSFER", 0.05),
                ("CASH_ON_DELIVERY", 0.1),
            ],
            "shipping_methods": [
                ("STANDARD", 0.5),
                ("EXPRESS", 0.2),
                ("OVERNIGHT", 0.05),
                ("TWO_DAY", 0.1),
                ("INTERNATIONAL", 0.05),
                ("LOCAL_PICKUP", 0.1),
            ],
        }
        
        # Also set default shipping costs
        if data_type == "shipping_methods":
            cls._SHIPPING_COSTS_CACHE["global"] = {
                "STANDARD": (5.0, 10.0),
                "EXPRESS": (15.0, 25.0),
                "OVERNIGHT": (25.0, 50.0),
                "TWO_DAY": (12.0, 20.0),
                "INTERNATIONAL": (30.0, 100.0),
                "LOCAL_PICKUP": (0.0, 0.0),
            }
        
        return defaults.get(data_type, [])

    @classmethod
    def get_order_statuses(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get order statuses with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing order statuses and weights
        """
        return cls.load_data("order_statuses", dataset)

    @classmethod
    def get_payment_methods(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get payment methods with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing payment methods and weights
        """
        return cls.load_data("payment_methods", dataset)

    @classmethod
    def get_shipping_methods(cls, dataset: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get shipping methods with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing shipping methods and weights
        """
        return cls.load_data("shipping_methods", dataset)

    @classmethod
    def get_shipping_cost_range(cls, shipping_method: str, dataset: Optional[str] = None) -> Tuple[float, float]:
        """Get the min and max shipping cost for a specific shipping method.

        Args:
            shipping_method: The shipping method to get the cost range for
            dataset: Optional dataset code (country code)

        Returns:
            A tuple containing the min and max shipping cost
        """
        # Load shipping methods data to ensure shipping costs are loaded
        cls.load_data("shipping_methods", dataset)
        
        # Get the shipping costs
        dataset_key = dataset or "global"
        costs = cls._SHIPPING_COSTS_CACHE.get(dataset_key, {})
        
        # Return the cost range for the specified method, or default values
        return costs.get(shipping_method, (5.0, 15.0))