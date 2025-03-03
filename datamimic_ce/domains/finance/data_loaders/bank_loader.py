# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Bank data loader.

This module provides data loading functionality for bank-related data,
loading reference data from CSV files for bank information.
"""

from pathlib import Path
from typing import Any, ClassVar

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.utils.data_path_util import DataPathUtil
from datamimic_ce.utils.file_util import FileUtil


class BankDataLoader(BaseDataLoader):
    """Data loader for bank related data.

    This class loads bank information from CSV files and provides methods to access this data.
    """

    # Cache for loaded data
    _BANKS_CACHE: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _BANKS_BY_WEIGHT_CACHE: ClassVar[dict[str, list[tuple[dict[str, Any], float]]]] = {}
    _ACCOUNT_TYPES_CACHE: ClassVar[dict[str, list[tuple[str, float]]]] = {}

    @classmethod
    def _get_file_path_for_data_type(cls, data_type: str, dataset: str | None = None) -> str:
        """Get the file path for the specified data type.

        Args:
            data_type: The type of data to get the file path for
            dataset: Optional dataset code (country code)

        Returns:
            The file path for the data type
        """
        # Map of data types to their base file names
        file_map = {
            "banks": "finance/bank/banks",
            "account_types": "finance/account_types",
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
    def load_banks(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Load bank data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of bank dictionaries
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._BANKS_CACHE:
            return cls._BANKS_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path_for_data_type("banks", dataset)

        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_banks(dataset)
            cls._BANKS_CACHE[dataset_key] = default_data
            return default_data

        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)

            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_banks(dataset)
                cls._BANKS_CACHE[dataset_key] = default_data
                return default_data

            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)

            result = []

            # Process each row
            for row in data:
                bank = {}

                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        bank[key] = row[idx]

                # Add the bank to the result
                result.append(bank)

            # Cache the data
            cls._BANKS_CACHE[dataset_key] = result

            # Also load as weighted data
            cls._load_banks_by_weight(dataset)

            return result

        except Exception as e:
            print(f"Error loading bank data: {e}")
            default_data = cls._get_default_banks(dataset)
            cls._BANKS_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _load_banks_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Load bank data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing bank dictionaries and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._BANKS_BY_WEIGHT_CACHE:
            return cls._BANKS_BY_WEIGHT_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path_for_data_type("banks", dataset)

        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_banks_by_weight(dataset)
            cls._BANKS_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data

        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)

            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_banks_by_weight(dataset)
                cls._BANKS_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data

            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)

            # Skip if weight column doesn't exist
            if "weight" not in header_dict:
                default_data = cls._get_default_banks_by_weight(dataset)
                cls._BANKS_BY_WEIGHT_CACHE[dataset_key] = default_data
                return default_data

            weight_idx = header_dict["weight"]

            result = []

            # Process each row
            for row in data:
                bank = {}

                # Extract all fields from the row
                for key, idx in header_dict.items():
                    if key != "weight":  # Skip the weight field
                        bank[key] = row[idx]

                # Get the weight
                try:
                    weight = float(row[weight_idx])
                except (ValueError, TypeError):
                    weight = 1.0

                # Add the bank and weight to the result
                result.append((bank, weight))

            # Cache the data
            cls._BANKS_BY_WEIGHT_CACHE[dataset_key] = result

            return result

        except Exception as e:
            print(f"Error loading bank data with weights: {e}")
            default_data = cls._get_default_banks_by_weight(dataset)
            cls._BANKS_BY_WEIGHT_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _get_default_banks(cls, dataset: str | None = None) -> list[dict[str, Any]]:
        """Get default bank data for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of bank dictionaries
        """
        if dataset == "DE":
            return [
                {"name": "Deutsche Bank", "swift_code": "DEUTDEFF", "bic": "DEUTDEFF"},
                {"name": "Commerzbank", "swift_code": "COBADEFF", "bic": "COBADEFF"},
                {"name": "DZ Bank", "swift_code": "GENODEFF", "bic": "GENODEFF"},
                {"name": "Sparkasse", "swift_code": "SPKADE2H", "bic": "SPKADE2H"},
            ]
        else:  # Default to US
            return [
                {"name": "Bank of America", "swift_code": "BOFAUS3N", "routing_number": "026009593"},
                {"name": "Chase", "swift_code": "CHASUS33", "routing_number": "021000021"},
                {"name": "Wells Fargo", "swift_code": "WFBIUS6S", "routing_number": "121042882"},
                {"name": "Citibank", "swift_code": "CITIUS33", "routing_number": "021000089"},
            ]

    @classmethod
    def _get_default_banks_by_weight(cls, dataset: str | None = None) -> list[tuple[dict[str, Any], float]]:
        """Get default bank data with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing bank dictionaries and weights
        """
        if dataset == "DE":
            return [
                ({"name": "Deutsche Bank", "swift_code": "DEUTDEFF", "bic": "DEUTDEFF"}, 0.3),
                ({"name": "Commerzbank", "swift_code": "COBADEFF", "bic": "COBADEFF"}, 0.3),
                ({"name": "DZ Bank", "swift_code": "GENODEFF", "bic": "GENODEFF"}, 0.2),
                ({"name": "Sparkasse", "swift_code": "SPKADE2H", "bic": "SPKADE2H"}, 0.2),
            ]
        else:  # Default to US
            return [
                ({"name": "Bank of America", "swift_code": "BOFAUS3N", "routing_number": "026009593"}, 0.3),
                ({"name": "Chase", "swift_code": "CHASUS33", "routing_number": "021000021"}, 0.3),
                ({"name": "Wells Fargo", "swift_code": "WFBIUS6S", "routing_number": "121042882"}, 0.2),
                ({"name": "Citibank", "swift_code": "CITIUS33", "routing_number": "021000089"}, 0.2),
            ]

    @classmethod
    def load_account_types(cls, dataset: str | None = None) -> list[tuple[str, float]]:
        """Load account types with weights.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing account types and weights
        """
        # Use 'global' as the default dataset key
        dataset_key = dataset or "global"

        # Check if the data is already cached
        if dataset_key in cls._ACCOUNT_TYPES_CACHE:
            return cls._ACCOUNT_TYPES_CACHE[dataset_key]

        # Get the file path
        file_path = cls._get_file_path_for_data_type("account_types", dataset)

        # If file path is empty, return default data
        if not file_path:
            default_data = cls._get_default_account_types(dataset)
            cls._ACCOUNT_TYPES_CACHE[dataset_key] = default_data
            return default_data

        try:
            # Get the data file path using DataPathUtil
            data_file_path = DataPathUtil.get_data_file_path(file_path)

            if not Path(data_file_path).exists():
                # If file doesn't exist, return default data
                default_data = cls._get_default_account_types(dataset)
                cls._ACCOUNT_TYPES_CACHE[dataset_key] = default_data
                return default_data

            # Load data from CSV
            header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(data_file_path)

            result = []

            # Process each row
            for row in data:
                # Get the type and weight columns
                type_val = None
                weight = 1.0

                # Find the type column
                for key in header_dict.keys():
                    if key.lower() != "weight":
                        type_idx = header_dict[key]
                        type_val = row[type_idx]
                        break

                # Get the weight if it exists
                if "weight" in header_dict:
                    weight_idx = header_dict["weight"]
                    try:
                        weight = float(row[weight_idx])
                    except (ValueError, TypeError):
                        weight = 1.0

                if type_val is not None:
                    result.append((type_val, weight))

            # Cache the data
            cls._ACCOUNT_TYPES_CACHE[dataset_key] = result

            return result

        except Exception as e:
            print(f"Error loading account types: {e}")
            default_data = cls._get_default_account_types(dataset)
            cls._ACCOUNT_TYPES_CACHE[dataset_key] = default_data
            return default_data

    @classmethod
    def _get_default_account_types(cls, dataset: str | None = None) -> list[tuple[str, float]]:
        """Get default account types with weights for the specified dataset.

        Args:
            dataset: Optional dataset code (country code)

        Returns:
            A list of tuples containing account types and weights
        """
        if dataset == "DE":
            return [
                ("GIROKONTO", 0.4),
                ("SPARKONTO", 0.3),
                ("FESTGELDKONTO", 0.1),
                ("TAGESGELDKONTO", 0.1),
                ("DEPOT", 0.1),
            ]
        else:  # Default to US
            return [
                ("CHECKING", 0.4),
                ("SAVINGS", 0.3),
                ("MONEY_MARKET", 0.1),
                ("CERTIFICATE_OF_DEPOSIT", 0.1),
                ("INVESTMENT", 0.1),
            ]
