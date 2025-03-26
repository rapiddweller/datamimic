# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
import string
from typing import Any, TypeVar

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.models.person import Person
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
    @property_cache
    def device_id(self) -> str:
        """Generate a unique device ID.

        Returns:
            A string representing a device ID.
        """
        prefix = "DEV"
        random_digits = "".join(random.choices(string.digits, k=8))
        return f"{prefix}-{random_digits}"

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
        prefix = "".join(random.choices(string.ascii_uppercase, k=2))
        suffix = "".join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"

    @property
    @property_cache
    def serial_number(self) -> str:
        """Generate a serial number.

        Returns:
            A string representing a serial number.
        """
        # Format: MFG-YYYY-XXXXXXXX
        year = random.randint(2010, datetime.datetime.now().year)
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"MFG-{year}-{random_part}"

    @property
    @property_cache
    def manufacture_date(self) -> str:
        """Generate a manufacture date.

        Returns:
            A string representing a manufacture date in ISO format.
        """
        # Generate a date between 1 and 10 years ago
        days_ago = random.randint(365, 3650)
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")

    @property
    @property_cache
    def expiration_date(self) -> str:
        """Generate an expiration date.

        Returns:
            A string representing an expiration date in ISO format.
        """
        # Generate a date between 1 and 5 years in the future
        days_ahead = random.randint(365, 1825)
        date = datetime.datetime.now() + datetime.timedelta(days=days_ahead)
        return date.strftime("%Y-%m-%d")

    @property
    @property_cache
    def last_maintenance_date(self) -> str:
        """Generate a last maintenance date.

        Returns:
            A string representing a last maintenance date in ISO format.
        """
        # Generate a date between 1 and 180 days ago
        days_ago = random.randint(1, 180)
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")

    @property
    @property_cache
    def next_maintenance_date(self) -> str:
        """Generate a next maintenance date.

        Returns:
            A string representing a next maintenance date in ISO format.
        """
        # Generate a date between 1 and 180 days in the future
        days_ahead = random.randint(1, 180)
        date = datetime.datetime.now() + datetime.timedelta(days=days_ahead)
        return date.strftime("%Y-%m-%d")

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
        specs["power_supply"] = random.choice(["AC", "Battery", "AC/Battery"])
        specs["weight_kg"] = str(round(random.uniform(1.5, 200.0), 1))
        specs["dimensions_cm"] = f"{random.randint(20, 200)}x{random.randint(20, 200)}x{random.randint(20, 200)}"

        # Device-specific specifications
        device_type = self.device_type.lower()

        if "ventilator" in device_type:
            specs["flow_rate_lpm"] = str(random.randint(1, 60))
            specs["pressure_range_cmh2o"] = f"{random.randint(0, 5)}-{random.randint(30, 50)}"
            specs["modes"] = random.choice(
                [
                    "Volume Control, Pressure Control, SIMV",
                    "CPAP, BiPAP, APRV",
                    "Volume Control, Pressure Control, CPAP, BiPAP",
                ]
            )

        elif "mri" in device_type:
            specs["field_strength_tesla"] = random.choice(["1.5T", "3.0T", "7.0T"])
            specs["bore_diameter_cm"] = str(random.randint(60, 80))
            specs["gradient_strength_mtm"] = str(random.randint(20, 80))

        elif "x-ray" in device_type:
            specs["max_voltage_kv"] = str(random.randint(40, 150))
            specs["max_current_ma"] = str(random.randint(100, 1000))
            specs["detector_type"] = random.choice(["Flat Panel", "CCD", "CMOS"])

        elif "ultrasound" in device_type:
            specs["probe_types"] = random.choice(
                ["Linear, Convex, Phased Array", "Linear, Convex, Transvaginal", "Linear, Convex, Cardiac"]
            )
            specs["imaging_modes"] = random.choice(
                [
                    "B-Mode, M-Mode, Color Doppler",
                    "B-Mode, Color Doppler, Power Doppler",
                    "B-Mode, M-Mode, Color Doppler, Power Doppler",
                ]
            )
            specs["frequency_range_mhz"] = f"{random.randint(1, 5)}-{random.randint(10, 18)}"

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
