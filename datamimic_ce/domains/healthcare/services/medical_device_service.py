# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domains.healthcare.data_loaders.medical_device_loader import MedicalDeviceDataLoader
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice


class MedicalDeviceService:
    """Service for managing medical device data.

    This class provides methods to create, retrieve, and manage medical device data.
    It integrates the model, data loader, and generator components.
    """

    def __init__(self, class_factory_util=None):
        """Initialize the MedicalDeviceService.

        Args:
            class_factory_util: The class factory utility for creating related entities.
        """
        self.class_factory_util = class_factory_util
        self.generator = MedicalDeviceGenerator(class_factory_util=class_factory_util)
        self._devices: dict[str, MedicalDevice] = {}

    def create_device(self, locale: str = "en", dataset: str | None = None, **kwargs) -> MedicalDevice:
        """Create a new medical device.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A MedicalDevice instance.
        """
        device = self.generator.generate_device(locale=locale, dataset=dataset, **kwargs)
        self._devices[device.device_id] = device
        return device

    def get_device(self, device_id: str) -> MedicalDevice | None:
        """Get a medical device by ID.

        Args:
            device_id: The ID of the device to retrieve.

        Returns:
            The MedicalDevice instance if found, None otherwise.
        """
        return self._devices.get(device_id)

    def get_all_devices(self) -> list[MedicalDevice]:
        """Get all medical devices.

        Returns:
            A list of all MedicalDevice instances.
        """
        return list(self._devices.values())

    def create_batch(
        self,
        count: int = 100,
        locale: str = "en",
        dataset: str | None = None,
        device_types: list[str] | None = None,
        manufacturers: list[str] | None = None,
        locations: list[str] | None = None,
        statuses: list[str] | None = None,
        store_devices: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Create a batch of medical devices.

        Args:
            count: The number of medical devices to create.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            device_types: Optional list of device types to choose from.
            manufacturers: Optional list of manufacturers to choose from.
            locations: Optional list of locations to choose from.
            statuses: Optional list of statuses to choose from.
            store_devices: Whether to store the created devices in the service.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        devices_data = self.generator.generate_batch(
            count=count,
            locale=locale,
            dataset=dataset,
            device_types=device_types,
            manufacturers=manufacturers,
            locations=locations,
            statuses=statuses,
            **kwargs,
        )

        if store_devices:
            # Create and store actual device instances
            for device_data in devices_data:
                device = MedicalDevice(
                    class_factory_util=self.class_factory_util, locale=locale, dataset=dataset, **kwargs
                )
                # Populate the device with the generated data
                for key, value in device_data.items():
                    device._property_cache[key] = value

                # Use the device_id value from the data directly
                device_id = device_data.get("device_id")
                if device_id:
                    self._devices[device_id] = device

        return devices_data

    def create_related_devices(
        self,
        count: int = 3,
        base_device: MedicalDevice | None = None,
        locale: str = "en",
        dataset: str | None = None,
        same_manufacturer: bool = True,
        same_type: bool = False,
        store_devices: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Create a set of related medical devices.

        Args:
            count: The number of related devices to create.
            base_device: Optional base device to relate the new devices to.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            same_manufacturer: Whether the created devices should have the same manufacturer.
            same_type: Whether the created devices should have the same device type.
            store_devices: Whether to store the created devices in the service.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        devices_data = self.generator.generate_related_devices(
            count=count,
            base_device=base_device,
            locale=locale,
            dataset=dataset,
            same_manufacturer=same_manufacturer,
            same_type=same_type,
            **kwargs,
        )

        if store_devices:
            # Create and store actual device instances
            for device_data in devices_data:
                device = MedicalDevice(
                    class_factory_util=self.class_factory_util, locale=locale, dataset=dataset, **kwargs
                )
                # Populate the device with the generated data
                for key, value in device_data.items():
                    device._property_cache[key] = value

                # Use the device_id value from the data directly
                device_id = device_data.get("device_id")
                if device_id:
                    self._devices[device_id] = device

        return devices_data

    def create_device_family(
        self,
        family_size: int = 5,
        locale: str = "en",
        dataset: str | None = None,
        device_type: str | None = None,
        manufacturer: str | None = None,
        store_devices: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Create a family of medical devices with sequential model numbers.

        Args:
            family_size: The number of devices in the family.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            device_type: Optional device type for all devices in the family.
            manufacturer: Optional manufacturer for all devices in the family.
            store_devices: Whether to store the created devices in the service.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        devices_data = self.generator.generate_device_family(
            family_size=family_size,
            locale=locale,
            dataset=dataset,
            device_type=device_type,
            manufacturer=manufacturer,
            **kwargs,
        )

        if store_devices:
            # Create and store actual device instances
            for device_data in devices_data:
                device = MedicalDevice(
                    class_factory_util=self.class_factory_util, locale=locale, dataset=dataset, **kwargs
                )
                # Populate the device with the generated data
                for key, value in device_data.items():
                    device._property_cache[key] = value

                # Use the device_id value from the data directly
                device_id = device_data.get("device_id")
                if device_id:
                    self._devices[device_id] = device

        return devices_data

    def filter_devices_by_type(self, device_type: str) -> list[MedicalDevice]:
        """Filter devices by type.

        Args:
            device_type: The device type to filter by.

        Returns:
            A list of MedicalDevice instances with the specified type.
        """
        return [device for device in self._devices.values() if device.device_type == device_type]

    def filter_devices_by_manufacturer(self, manufacturer: str) -> list[MedicalDevice]:
        """Filter devices by manufacturer.

        Args:
            manufacturer: The manufacturer to filter by.

        Returns:
            A list of MedicalDevice instances with the specified manufacturer.
        """
        return [device for device in self._devices.values() if device.manufacturer == manufacturer]

    def filter_devices_by_status(self, status: str) -> list[MedicalDevice]:
        """Filter devices by status.

        Args:
            status: The status to filter by.

        Returns:
            A list of MedicalDevice instances with the specified status.
        """
        return [device for device in self._devices.values() if device.status == status]

    def filter_devices_by_location(self, location: str) -> list[MedicalDevice]:
        """Filter devices by location.

        Args:
            location: The location to filter by.

        Returns:
            A list of MedicalDevice instances with the specified location.
        """
        return [device for device in self._devices.values() if device.location == location]

    def get_device_types(self, country_code: str = "US") -> list[str]:
        """Get available device types.

        Args:
            country_code: The country code to use for loading data.

        Returns:
            A list of device types.
        """
        loader = MedicalDeviceDataLoader(country_code=country_code)
        return loader.load_device_types()

    def get_manufacturers(self, country_code: str = "US") -> list[str]:
        """Get available manufacturers.

        Args:
            country_code: The country code to use for loading data.

        Returns:
            A list of manufacturers.
        """
        loader = MedicalDeviceDataLoader(country_code=country_code)
        return loader.load_manufacturers()

    def get_locations(self, country_code: str = "US") -> list[str]:
        """Get available locations.

        Args:
            country_code: The country code to use for loading data.

        Returns:
            A list of locations.
        """
        loader = MedicalDeviceDataLoader(country_code=country_code)
        return loader.load_locations()

    def get_statuses(self) -> list[str]:
        """Get available statuses.

        Returns:
            A list of statuses.
        """
        loader = MedicalDeviceDataLoader()
        return loader.load_statuses()

    def clear_devices(self) -> None:
        """Clear all stored devices."""
        self._devices.clear()
