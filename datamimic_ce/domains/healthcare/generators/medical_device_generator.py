# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice


class MedicalDeviceGenerator:
    """Generator for medical device data.

    This class provides methods to generate single or multiple medical device instances.
    It supports customization of the generation process through various parameters.
    """

    def __init__(self, class_factory_util=None):
        """Initialize the MedicalDeviceGenerator.

        Args:
            class_factory_util: The class factory utility for creating related entities.
        """
        self.class_factory_util = class_factory_util

    def generate_device(self, locale: str = "en", dataset: str | None = None, **kwargs) -> MedicalDevice:
        """Generate a single medical device.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A MedicalDevice instance.
        """
        return MedicalDevice(class_factory_util=self.class_factory_util, locale=locale, dataset=dataset, **kwargs)

    def generate_batch(
        self,
        count: int = 100,
        locale: str = "en",
        dataset: str | None = None,
        device_types: list[str] | None = None,
        manufacturers: list[str] | None = None,
        locations: list[str] | None = None,
        statuses: list[str] | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Generate a batch of medical devices.

        Args:
            count: The number of medical devices to generate.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            device_types: Optional list of device types to choose from.
            manufacturers: Optional list of manufacturers to choose from.
            locations: Optional list of locations to choose from.
            statuses: Optional list of statuses to choose from.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        result = []

        # Create a single device instance to reuse
        device = self.generate_device(locale=locale, dataset=dataset, **kwargs)

        # Override the DATA_CACHE if custom values are provided
        if device_types:
            MedicalDevice._DATA_CACHE["device_types"] = device_types
        if manufacturers:
            MedicalDevice._DATA_CACHE["manufacturers"] = manufacturers
        if locations:
            MedicalDevice._DATA_CACHE["locations"] = locations
        if statuses:
            MedicalDevice._DATA_CACHE["statuses"] = statuses

        # Generate the batch
        for _ in range(count):
            device.reset()
            result.append(device.to_dict())

        return result

    def generate_related_devices(
        self,
        count: int = 3,
        base_device: MedicalDevice | None = None,
        locale: str = "en",
        dataset: str | None = None,
        same_manufacturer: bool = True,
        same_type: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Generate a set of related medical devices.

        Args:
            count: The number of related devices to generate.
            base_device: Optional base device to relate the new devices to.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            same_manufacturer: Whether the generated devices should have the same manufacturer.
            same_type: Whether the generated devices should have the same device type.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        result = []

        # Create a base device if not provided
        if not base_device:
            base_device = self.generate_device(locale=locale, dataset=dataset, **kwargs)

        # Get the base device's manufacturer and type if needed
        base_manufacturer = base_device.manufacturer if same_manufacturer else None
        base_type = base_device.device_type if same_type else None

        # Add the base device to the result
        result.append(base_device.to_dict())

        # Generate related devices
        for _ in range(count - 1):  # -1 because we already added the base device
            device = self.generate_device(locale=locale, dataset=dataset, **kwargs)
            device.reset()

            # Override manufacturer if needed
            if same_manufacturer:
                device._property_cache["manufacturer"] = base_manufacturer

            # Override device type if needed
            if same_type:
                device._property_cache["device_type"] = base_type

            result.append(device.to_dict())

        return result

    def generate_device_family(
        self,
        family_size: int = 5,
        locale: str = "en",
        dataset: str | None = None,
        device_type: str | None = None,
        manufacturer: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Generate a family of medical devices with sequential model numbers.

        Args:
            family_size: The number of devices in the family.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            device_type: Optional device type for all devices in the family.
            manufacturer: Optional manufacturer for all devices in the family.
            **kwargs: Additional keyword arguments to pass to the MedicalDevice constructor.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        result = []

        # Create a base device
        base_device = self.generate_device(locale=locale, dataset=dataset, **kwargs)

        # Set the device type and manufacturer if provided
        if device_type:
            base_device._property_cache["device_type"] = device_type
        if manufacturer:
            base_device._property_cache["manufacturer"] = manufacturer

        # Get the base model number prefix (first 2 characters)
        base_model_prefix = base_device.model_number[:2]

        # Generate the family
        for i in range(family_size):
            # Create a new device for each family member
            device = self.generate_device(locale=locale, dataset=dataset, **kwargs)
            device.reset()

            # Set the same device type and manufacturer
            device._property_cache["device_type"] = base_device.device_type
            device._property_cache["manufacturer"] = base_device.manufacturer

            # Create a sequential model number
            sequential_number = f"{1000 + i:04d}"
            device._property_cache["model_number"] = f"{base_model_prefix}{sequential_number}"

            result.append(device.to_dict())

        return result
