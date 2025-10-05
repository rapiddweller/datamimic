# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
from typing import Any, TypeVar

from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator

T = TypeVar("T")


class MedicalDevice(BaseEntity):
    """Generate medical device data.

    This class generates realistic medical device data including device IDs,
    types, manufacturers, model numbers, serial numbers, dates, statuses,
    locations, specifications, usage logs, and maintenance history.

    Data is loaded from country-specific CSV files when available,
    falling back to generic data files if needed.
    """

    # Module-level cache for data to reduce file I/O

    def __init__(self, medical_device_generator: MedicalDeviceGenerator):
        """Initialize the MedicalDevice.

        Args:
            medical_device_generator: The medical device generator.
        """
        super().__init__()
        self._medical_device_generator = medical_device_generator

    @property
    def dataset(self) -> str:
        return self._medical_device_generator.dataset  #  use generator property; avoid private attr

    @property
    @property_cache
    def device_id(self) -> str:
        """Generate a unique device ID.

        Returns:
            A string representing a device ID.
        """
        rng = self._medical_device_generator.rng
        suffix = "".join(str(rng.randint(0, 9)) for _ in range(8))
        return f"DEV-{suffix}"

    @property
    @property_cache
    def device_type(self) -> str:
        """Generate a device type.

        Returns:
            A string representing a device type.
        """
        return self._medical_device_generator.generate_device_type()

    @property
    @property_cache
    def manufacturer(self) -> str:
        """Generate a manufacturer name.

        Returns:
            A string representing a manufacturer name.
        """
        return self._medical_device_generator.generate_manufacturer()

    @property
    @property_cache
    def model_number(self) -> str:
        """Generate a model number.

        Returns:
            A string representing a model number.
        """
        rng = self._medical_device_generator.rng
        letters = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(2))
        digits = "".join(str(rng.randint(0, 9)) for _ in range(4))
        return f"{letters}{digits}"

    @property
    @property_cache
    def serial_number(self) -> str:
        """Generate a serial number.

        Returns:
            A string representing a serial number.
        """
        # Format: MFG-YYYY-XXXXXXXX
        year = self._medical_device_generator.rng.randint(2010, datetime.datetime.now().year)
        rng = self._medical_device_generator.rng
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        random_part = "".join(rng.choice(alphabet) for _ in range(8))
        return f"MFG-{year}-{random_part}"

    @property
    @property_cache
    def manufacture_date(self) -> str:
        """Generate a manufacture date.

        Returns:
            A string representing a manufacture date in ISO format.
        """
        #  delegate to generator for SOC and determinism
        return self._medical_device_generator.generate_manufacture_date()

    @property
    @property_cache
    def expiration_date(self) -> str:
        """Generate an expiration date.

        Returns:
            A string representing an expiration date in ISO format.
        """
        return self._medical_device_generator.generate_expiration_date()

    @property
    @property_cache
    def last_maintenance_date(self) -> str:
        """Generate a last maintenance date.

        Returns:
            A string representing a last maintenance date in ISO format.
        """
        return self._medical_device_generator.generate_last_maintenance_date()

    @property
    @property_cache
    def next_maintenance_date(self) -> str:
        """Generate a next maintenance date.

        Returns:
            A string representing a next maintenance date in ISO format.
        """
        return self._medical_device_generator.generate_next_maintenance_date()

    @property
    @property_cache
    def status(self) -> str:
        """Generate a device status.

        Returns:
            A string representing a device status.
        """
        return self._medical_device_generator.generate_device_status()

    @property
    @property_cache
    def location(self) -> str:
        """Generate a device location.

        Returns:
            A string representing a device location.
        """
        return self._medical_device_generator.generate_location()

    @property
    @property_cache
    def assigned_to(self) -> str:
        """Generate a name of the person the device is assigned to.

        Returns:
            A string representing a person's name.
        """
        assigned_person = Person(self._medical_device_generator.person_generator)
        return assigned_person.name

    @property
    @property_cache
    def specifications(self) -> dict[str, str]:
        """Generate device specifications.

        Returns:
            A dictionary of device specifications.
        """
        specs = {}

        # Common specifications for all devices
        rng = self._medical_device_generator.rng
        specs["power_supply"] = rng.choice(["AC", "Battery", "AC/Battery"])
        specs["weight_kg"] = str(round(rng.uniform(1.5, 200.0), 1))
        specs["dimensions_cm"] = f"{rng.randint(20, 200)}x{rng.randint(20, 200)}x{rng.randint(20, 200)}"

        # Device-specific specifications
        device_type = self.device_type.lower()

        if "ventilator" in device_type:
            specs["flow_rate_lpm"] = str(rng.randint(1, 60))
            specs["pressure_range_cmh2o"] = f"{rng.randint(0, 5)}-{rng.randint(30, 50)}"
            specs["modes"] = self._medical_device_generator.pick_ventilator_mode()

        elif "mri" in device_type:
            specs["field_strength_tesla"] = self._medical_device_generator.pick_mri_field_strength()
            specs["bore_diameter_cm"] = str(rng.randint(60, 80))
            specs["gradient_strength_mtm"] = str(rng.randint(20, 80))

        elif "x-ray" in device_type:
            specs["max_voltage_kv"] = str(rng.randint(40, 150))
            specs["max_current_ma"] = str(rng.randint(100, 1000))
            specs["detector_type"] = self._medical_device_generator.pick_xray_detector_type()

        elif "ultrasound" in device_type:
            specs["probe_types"] = self._medical_device_generator.pick_ultrasound_probe_type()
            specs["imaging_modes"] = self._medical_device_generator.pick_ultrasound_imaging_mode()
            specs["frequency_range_mhz"] = f"{rng.randint(1, 5)}-{rng.randint(10, 18)}"

        return specs

    @property
    @property_cache
    def usage_logs(self) -> list[dict[str, str]]:
        """Generate device usage logs.

        Returns:
            A list of dictionaries representing usage logs.
        """
        return self._medical_device_generator.generate_usage_log(self.assigned_to, self.device_type)

    @property
    @property_cache
    def maintenance_history(self) -> list[dict[str, Any]]:
        """Generate device maintenance history.

        Returns:
            A list of dictionaries representing maintenance history.
        """
        return self._medical_device_generator.generate_maintenance_history()

    def to_dict(self) -> dict[str, Any]:
        """Convert the medical device to a dictionary.

        Returns:
            A dictionary representation of the medical device.
        """
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "serial_number": self.serial_number,
            "manufacture_date": self.manufacture_date,
            "expiration_date": self.expiration_date,
            "last_maintenance_date": self.last_maintenance_date,
            "next_maintenance_date": self.next_maintenance_date,
            "status": self.status,
            "location": self.location,
            "assigned_to": self.assigned_to,
            "specifications": self.specifications,
            "usage_logs": self.usage_logs,
            "maintenance_history": self.maintenance_history,
        }
