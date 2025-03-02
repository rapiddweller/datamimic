# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Public Sector data loader.

This module provides a base data loading functionality for public sector-related data,
serving as a foundation for police, education, and administration data loaders.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, cast

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class PublicSectorDataLoader(BaseDataLoader):
    """Base data loader for public sector related data.

    This class loads public sector data from CSV files and provides methods to access this data.
    """

    @classmethod
    def _get_file_path(cls, base_path: str, data_type: str, dataset: Optional[str] = None) -> str:
        """Get the file path for the specified data type.

        Args:
            base_path: The base path for the data (e.g., 'public_sector/police')
            data_type: The specific data type to get the file path for
            dataset: Optional dataset code (country code)

        Returns:
            The file path for the data type
        """
        # Construct the file path
        if dataset:
            file_path = f"{base_path}/{data_type}_{dataset}.csv"
        else:
            # First try with 'US' as default dataset
            file_path = f"{base_path}/{data_type}_US.csv"
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            if Path(data_file_path).exists():
                return file_path
            # Fallback to generic file without country code
            file_path = f"{base_path}/{data_type}.csv"
        
        return file_path

    @classmethod
    def _load_data(cls, file_path: str) -> List[Dict[str, Any]]:
        """Load data from a CSV file.

        Args:
            file_path: The path to the CSV file to load

        Returns:
            A list of dictionaries containing the data from the CSV file
        """
        try:
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                return []
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            result = []
            
            # Process each row
            for row in data:
                item = {}
                
                # Extract all fields from the row, except weight
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        item[key] = row[idx]
                
                # Add the item to the result
                result.append(item)
            
            return result
        
        except Exception as e:
            print(f"Error loading data from {file_path}: {e}")
            return []

    @classmethod
    def _load_data_with_weight(cls, file_path: str) -> List[Tuple[Dict[str, Any], float]]:
        """Load data with weights from a CSV file.

        Args:
            file_path: The path to the CSV file to load

        Returns:
            A list of tuples containing dictionaries and weights
        """
        try:
            data_file_path = DataPathUtil.get_data_file_path(file_path)
            
            if not Path(data_file_path).exists():
                return []
            
            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)
            
            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                # Create data with equal weights
                items = cls._load_data(file_path)
                weight = 1.0 / len(items) if items else 0.0
                return [(item, weight) for item in items]
            
            weight_idx = header_dict["weight"]
            
            result = []
            
            # Process each row
            for row in data:
                item = {}
                
                # Extract all fields from the row, except weight
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        item[key] = row[idx]
                
                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0
                
                # Add the item and weight to the result
                result.append((item, weight))
            
            return result
        
        except Exception as e:
            print(f"Error loading data with weights from {file_path}: {e}")
            return []