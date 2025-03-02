# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
import string
from pathlib import Path
from typing import Any, TypeVar

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import property_cache
from datamimic_ce.domains.common.models.person import Person
from datamimic_ce.logger import logger

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
    _DATA_CACHE: dict[str, list[Any]] = {}

    def __init__(self, class_factory_util=None, locale: str = "en", dataset: str | None = None, **kwargs):
        """Initialize the MedicalDevice.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale  # Ensure _locale is set to the passed locale parameter
        self._dataset = dataset  # Ensure _dataset is set to the passed dataset parameter

        # Determine country code from dataset or locale
        self._country_code = self._determine_country_code(dataset, locale)

        # Load data if not already loaded
        if not self._DATA_CACHE:
            self._load_data(self._country_code)

        # Initialize property cache
        self._property_cache = {}

    def _determine_country_code(self, dataset: str | None, locale: str) -> str:
        """Determine the country code from the dataset or locale.

        Args:
            dataset: The dataset to use for generating data.
            locale: The locale to use for generating data.

        Returns:
            The country code.
        """
        if dataset:
            # Extract country code from dataset name if possible
            parts = dataset.split("_")
            if len(parts) > 1 and len(parts[-1]) == 2:
                return parts[-1].upper()

        # Fall back to locale-based determination
        if locale and "_" in locale:
            country_code = locale.split("_")[1].upper()
            return country_code

        # Default to US if no country code can be determined
        return "US"

    @classmethod
    def _load_data(cls, country_code: str = "US") -> None:
        """Load data from CSV files.

        Args:
            country_code: The country code to use for loading data.
        """
        # Define base path for data files
        base_path = Path(__file__).parent.parent.parent.parent / "entities" / "data" / "medical_device"

        # Define file paths for different data types
        device_types_path = base_path / f"device_types_{country_code}.csv"
        manufacturers_path = base_path / f"manufacturers_{country_code}.csv"
        locations_path = base_path / f"locations_{country_code}.csv"
        statuses_path = base_path / "statuses.csv"

        # Load device types with fallback
        if device_types_path.exists():
            cls._DATA_CACHE["device_types"] = cls._load_simple_csv(device_types_path)
        else:
            fallback_path = base_path / "device_types_US.csv"
            if fallback_path.exists():
                cls._DATA_CACHE["device_types"] = cls._load_simple_csv(fallback_path)
            else:
                logger.warning(f"No device types data found for {country_code}, using default values")
                cls._DATA_CACHE["device_types"] = ["Ventilator", "MRI Scanner", "X-Ray Machine", "Ultrasound"]

        # Load manufacturers with fallback
        if manufacturers_path.exists():
            cls._DATA_CACHE["manufacturers"] = cls._load_simple_csv(manufacturers_path)
        else:
            fallback_path = base_path / "manufacturers_US.csv"
            if fallback_path.exists():
                cls._DATA_CACHE["manufacturers"] = cls._load_simple_csv(fallback_path)
            else:
                logger.warning(f"No manufacturers data found for {country_code}, using default values")
                cls._DATA_CACHE["manufacturers"] = ["MedTech Inc.", "HealthCare Systems", "BioMed Solutions"]

        # Load locations with fallback
        if locations_path.exists():
            cls._DATA_CACHE["locations"] = cls._load_simple_csv(locations_path)
        else:
            fallback_path = base_path / "locations_US.csv"
            if fallback_path.exists():
                cls._DATA_CACHE["locations"] = cls._load_simple_csv(fallback_path)
            else:
                logger.warning(f"No locations data found for {country_code}, using default values")
                cls._DATA_CACHE["locations"] = ["Operating Room", "ICU", "Emergency Department", "Radiology"]

        # Load statuses (not country-specific)
        if statuses_path.exists():
            cls._DATA_CACHE["statuses"] = cls._load_simple_csv(statuses_path)
        else:
            cls._DATA_CACHE["statuses"] = ["Active", "Maintenance", "Retired", "Defective"]

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load data from a simple CSV file.

        Args:
            file_path: The path to the CSV file.

        Returns:
            A list of strings, each representing a line from the CSV file.
        """
        try:
            with open(file_path, encoding="utf-8") as file:
                # Skip header row and read data
                lines = file.readlines()
                if lines:
                    # Remove header if it exists
                    if lines and lines[0].strip().lower() in ["name", "type", "value", "location", "status", "header"]:
                        lines = lines[1:]

                    # Clean up lines and return
                    return [line.strip() for line in lines if line.strip()]
                return []
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []

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
        device_types = self._DATA_CACHE.get("device_types", ["Ventilator", "MRI Scanner", "X-Ray Machine"])
        return random.choice(device_types)

    @property
    @property_cache
    def manufacturer(self) -> str:
        """Generate a manufacturer name.

        Returns:
            A string representing a manufacturer name.
        """
        manufacturers = self._DATA_CACHE.get("manufacturers", ["MedTech Inc.", "HealthCare Systems"])
        return random.choice(manufacturers)

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
        statuses = self._DATA_CACHE.get("statuses", ["Active", "Maintenance", "Retired", "Defective"])
        return random.choice(statuses)

    @property
    @property_cache
    def location(self) -> str:
        """Generate a device location.

        Returns:
            A string representing a device location.
        """
        locations = self._DATA_CACHE.get("locations", ["Operating Room", "ICU", "Emergency Department"])
        return random.choice(locations)

    @property
    @property_cache
    def assigned_to(self) -> str:
        """Generate a name of the person the device is assigned to.

        Returns:
            A string representing a person's name.
        """
        if self._class_factory_util:
            person = self._class_factory_util.create_instance(Person, locale=self._locale, dataset=self._dataset)
            return f"{person.first_name} {person.last_name}"
        return "Unassigned"

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
        logs = []

        # Generate between 3 and 10 usage logs
        num_logs = random.randint(3, 10)

        # Start date for logs (between 1 and 2 years ago)
        start_days_ago = random.randint(365, 730)
        current_date = datetime.datetime.now() - datetime.timedelta(days=start_days_ago)

        for _ in range(num_logs):
            # Move forward in time for each log
            days_forward = random.randint(5, 60)
            current_date += datetime.timedelta(days=days_forward)

            # Skip if we've gone past today
            if current_date > datetime.datetime.now():
                break

            # Generate a log entry
            log_entry = {
                "date": current_date.strftime("%Y-%m-%d"),
                "user": self._generate_user_name(),
                "duration_minutes": str(random.randint(15, 240)),
                "purpose": self._generate_usage_purpose(),
                "notes": self._generate_usage_notes(),
            }

            logs.append(log_entry)

        return logs

    def _generate_user_name(self) -> str:
        """Generate a user name for usage logs.

        Returns:
            A string representing a user name.
        """
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia"]

        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_usage_purpose(self) -> str:
        """Generate a purpose for device usage.

        Returns:
            A string representing a usage purpose.
        """
        device_type = self.device_type.lower()

        purposes = [
            "Routine patient care",
            "Emergency procedure",
            "Scheduled examination",
            "Training session",
            "Diagnostic procedure",
        ]

        # Add device-specific purposes
        if "ventilator" in device_type:
            purposes.extend(["Respiratory support", "Post-surgical ventilation", "Critical care support"])
        elif "mri" in device_type:
            purposes.extend(["Brain scan", "Spinal examination", "Musculoskeletal imaging", "Abdominal scan"])
        elif "x-ray" in device_type:
            purposes.extend(
                ["Chest radiograph", "Bone fracture assessment", "Foreign body detection", "Dental imaging"]
            )
        elif "ultrasound" in device_type:
            purposes.extend(["Pregnancy examination", "Abdominal assessment", "Cardiac evaluation", "Vascular study"])

        return random.choice(purposes)

    def _generate_usage_notes(self) -> str:
        """Generate notes for device usage.

        Returns:
            A string representing usage notes.
        """
        notes_options = [
            "Device performed as expected.",
            "Minor calibration issues noted.",
            "Patient examination completed successfully.",
            "Procedure went smoothly.",
            "Device required restart during procedure.",
            "Image quality excellent.",
            "Some interference observed.",
            "Routine usage, no issues.",
            "Training session for new staff.",
            "Maintenance check performed before use.",
        ]

        # 20% chance of no notes
        if random.random() < 0.2:
            return ""

        return random.choice(notes_options)

    @property
    @property_cache
    def maintenance_history(self) -> list[dict[str, Any]]:
        """Generate device maintenance history.

        Returns:
            A list of dictionaries representing maintenance history.
        """
        history = []

        # Generate between 2 and 8 maintenance records
        num_records = random.randint(2, 8)

        # Start date for maintenance (between 1 and 3 years ago)
        start_days_ago = random.randint(365, 1095)
        current_date = datetime.datetime.now() - datetime.timedelta(days=start_days_ago)

        for _ in range(num_records):
            # Move forward in time for each maintenance
            days_forward = random.randint(30, 180)
            current_date += datetime.timedelta(days=days_forward)

            # Skip if we've gone past today
            if current_date > datetime.datetime.now():
                break

            # Generate a maintenance record
            maintenance_record = {
                "date": current_date.strftime("%Y-%m-%d"),
                "technician": self._generate_technician_name(),
                "type": self._generate_maintenance_type(),
                "parts_replaced": self._generate_parts_replaced(),
                "cost": self._generate_maintenance_cost(),
                "duration_hours": round(random.uniform(0.5, 8.0), 1),
                "result": self._generate_maintenance_result(),
                "notes": self._generate_maintenance_notes(),
            }

            history.append(maintenance_record)

        return history

    def _generate_technician_name(self) -> str:
        """Generate a technician name for maintenance history.

        Returns:
            A string representing a technician name.
        """
        first_names = ["Alex", "Sam", "Jordan", "Casey", "Taylor", "Morgan", "Riley", "Jamie"]
        last_names = ["Tech", "Service", "Repair", "Maintenance", "Support", "Systems", "Engineering"]

        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_maintenance_type(self) -> str:
        """Generate a maintenance type.

        Returns:
            A string representing a maintenance type.
        """
        types = [
            "Routine inspection",
            "Preventive maintenance",
            "Calibration",
            "Software update",
            "Hardware repair",
            "Component replacement",
            "Emergency repair",
            "Safety check",
        ]

        return random.choice(types)

    def _generate_parts_replaced(self) -> list[str]:
        """Generate a list of parts replaced during maintenance.

        Returns:
            A list of strings representing parts replaced.
        """
        all_parts = [
            "Power supply",
            "Battery",
            "Display screen",
            "Control board",
            "Sensor array",
            "Cooling fan",
            "Cable assembly",
            "User interface panel",
            "Memory module",
            "Network card",
            "Filter assembly",
            "Pump mechanism",
            "Valve system",
        ]

        # 40% chance of no parts replaced
        if random.random() < 0.4:
            return []

        # Otherwise, replace 1-3 parts
        num_parts = random.randint(1, 3)
        return random.sample(all_parts, min(num_parts, len(all_parts)))

    def _generate_maintenance_cost(self) -> float:
        """Generate a maintenance cost.

        Returns:
            A float representing a maintenance cost.
        """
        # Base cost between $100 and $500
        base_cost = random.uniform(100, 500)

        # If parts were replaced, add more cost
        if random.random() < 0.6:  # 60% chance of parts replacement
            parts_cost = random.uniform(200, 2000)
            return round(base_cost + parts_cost, 2)

        return round(base_cost, 2)

    def _generate_maintenance_result(self) -> str:
        """Generate a maintenance result.

        Returns:
            A string representing a maintenance result.
        """
        results = [
            "Completed successfully",
            "Issues resolved",
            "Partial repair - follow-up needed",
            "Temporary fix applied",
            "No issues found",
            "Calibration completed",
            "Software updated",
            "Hardware replaced",
            "Referred to manufacturer",
        ]

        return random.choice(results)

    def _generate_maintenance_notes(self) -> str:
        """Generate notes for maintenance history.

        Returns:
            A string representing maintenance notes.
        """
        notes_options = [
            "Device operating within normal parameters after service.",
            "Recommended replacement within next 6 months.",
            "Firmware updated to latest version.",
            "Calibration values adjusted to meet specifications.",
            "User reported intermittent issues that could not be replicated.",
            "Preventive maintenance completed according to schedule.",
            "Device showing signs of wear but still functional.",
            "Emergency repair completed, follow-up inspection recommended.",
            "All safety checks passed.",
            "Maintenance performed according to manufacturer guidelines.",
        ]

        # 10% chance of no notes
        if random.random() < 0.1:
            return ""

        return random.choice(notes_options)

    def reset(self) -> None:
        """Reset all cached properties."""
        # Clear the property cache
        self._property_cache = {}

        # Clear all property caches by removing the cache attributes
        for attr_name in list(self.__dict__.keys()):
            if attr_name.endswith("_cache") and attr_name != "_property_cache":
                delattr(self, attr_name)

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

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of medical devices.

        Args:
            count: The number of medical devices to generate.

        Returns:
            A list of dictionaries, each representing a medical device.
        """
        devices = []
        for _ in range(count):
            # Reset the device to generate new values
            self.reset()
            # Convert to dictionary and add to the list
            devices.append(self.to_dict())
        return devices
