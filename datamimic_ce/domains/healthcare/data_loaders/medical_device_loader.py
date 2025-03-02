# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.core.base_data_loader import BaseDataLoader
from datamimic_ce.logger import logger


class MedicalDeviceDataLoader(BaseDataLoader):
    """Data loader for medical device data.

    This class is responsible for loading medical device data from CSV files.
    It provides methods to load device types, manufacturers, locations, and statuses.
    """

    def __init__(self, country_code: str = "US"):
        """Initialize the MedicalDeviceDataLoader.

        Args:
            country_code: The country code to use for loading data.
        """
        super().__init__()
        self.country_code = country_code
        self._data_cache: dict[str, list[str]] = {}

    def load_device_types(self) -> list[str]:
        """Load device types from CSV file.

        Returns:
            A list of device types.
        """
        return self._load_data_with_fallback("device_types")

    def load_manufacturers(self) -> list[str]:
        """Load manufacturers from CSV file.

        Returns:
            A list of manufacturers.
        """
        return self._load_data_with_fallback("manufacturers")

    def load_locations(self) -> list[str]:
        """Load locations from CSV file.

        Returns:
            A list of locations.
        """
        return self._load_data_with_fallback("locations")

    def load_statuses(self) -> list[str]:
        """Load statuses from CSV file.

        Returns:
            A list of statuses.
        """
        # Statuses are not country-specific
        if "statuses" not in self._data_cache:
            base_path = self._get_base_path()
            statuses_path = base_path / "device_statuses_US.csv"

            if statuses_path.exists():
                self._data_cache["statuses"] = self._load_simple_csv(statuses_path)
            else:
                logger.warning("No statuses data found, using default values")
                self._data_cache["statuses"] = ["Active", "Maintenance", "Retired", "Defective"]

        return self._data_cache["statuses"]

    def _load_data_with_fallback(self, data_type: str) -> list[str]:
        """Load data with fallback to US data if country-specific data is not available.

        Args:
            data_type: The type of data to load (e.g., "device_types", "manufacturers").

        Returns:
            A list of data items.
        """
        if data_type not in self._data_cache:
            base_path = self._get_base_path()
            data_path = base_path / f"{data_type}_{self.country_code}.csv"

            if data_path.exists():
                self._data_cache[data_type] = self._load_simple_csv(data_path)
            else:
                # Fallback to US data
                fallback_path = base_path / f"{data_type}_US.csv"
                if fallback_path.exists():
                    self._data_cache[data_type] = self._load_simple_csv(fallback_path)
                else:
                    logger.warning(f"No {data_type} data found for {self.country_code}, using default values")
                    self._data_cache[data_type] = self._get_default_values(data_type)

        return self._data_cache[data_type]

    def _get_base_path(self) -> Path:
        """Get the base path for data files.

        Returns:
            The base path for data files.
        """
        return Path(__file__).parent.parent.parent.parent / "data" / "healthcare" / "medical_device"

    def _get_default_values(self, data_type: str) -> list[str]:
        """Get default values for a data type.

        Args:
            data_type: The type of data to get default values for.

        Returns:
            A list of default values.
        """
        defaults = {
            "device_types": ["Ventilator", "MRI Scanner", "X-Ray Machine", "Ultrasound"],
            "manufacturers": ["MedTech Inc.", "HealthCare Systems", "BioMed Solutions"],
            "locations": ["Operating Room", "ICU", "Emergency Department", "Radiology"],
            "statuses": ["Active", "Maintenance", "Retired", "Defective"],
        }

        return defaults.get(data_type, [])
