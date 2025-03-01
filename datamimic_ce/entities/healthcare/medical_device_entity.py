# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
import string
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.person_entity import PersonEntity
from datamimic_ce.logger import logger

T = TypeVar("T")


class MedicalDeviceEntity(Entity):
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
        """Initialize the MedicalDeviceEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util

        # Determine country code from dataset or locale
        self._country_code = self._determine_country_code(dataset, locale)

        # Get optional parameters
        self._device_type = kwargs.get("device_type")
        self._manufacturer = kwargs.get("manufacturer")
        self._status = kwargs.get("status")
        self._location = kwargs.get("location")

        # Create person entity for technician name generation
        if class_factory_util:
            self._person_entity = PersonEntity(class_factory_util, locale=locale, dataset=dataset)

        # Load data from CSV files
        self._load_data(self._country_code)

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "device_id": self._generate_device_id,
                "device_type": self._generate_device_type,
                "manufacturer": self._generate_manufacturer,
                "model_number": self._generate_model_number,
                "serial_number": self._generate_serial_number,
                "manufacture_date": self._generate_manufacture_date,
                "expiration_date": self._generate_expiration_date,
                "last_maintenance_date": self._generate_last_maintenance_date,
                "next_maintenance_date": self._generate_next_maintenance_date,
                "status": self._generate_status,
                "location": self._generate_location,
                "assigned_to": self._generate_assigned_to,
                "specifications": self._generate_specifications,
                "usage_logs": self._generate_usage_logs,
                "maintenance_history": self._generate_maintenance_history,
            }
        )

        # Cache for entity properties
        self._property_cache: dict[str, Any] = {}

    def _determine_country_code(self, dataset: str | None, locale: str) -> str:
        """Determine the country code to use based on dataset and locale.

        Args:
            dataset: The dataset parameter.
            locale: The locale parameter.

        Returns:
            A two-letter country code.
        """
        # If dataset is provided, prioritize it
        if dataset and len(dataset) == 2:
            return dataset.upper()

        # Try to extract country code from locale
        if locale:
            # Check for formats like "en_US" or "de-DE"
            if "_" in locale and len(locale.split("_")) > 1:
                country_part = locale.split("_")[1]
                if len(country_part) == 2:
                    return country_part.upper()
            elif "-" in locale and len(locale.split("-")) > 1:
                country_part = locale.split("-")[1]
                if len(country_part) == 2:
                    return country_part.upper()

            # Direct matching for 2-letter codes
            if len(locale) == 2:
                # Don't use the 2-letter code as country directly
                # Instead use the language mapping below
                pass

            # Map common language codes to countries
            language_code = locale.split("_")[0].split("-")[0].lower()
            language_map = {
                "en": "US",
                "de": "DE",
                "fr": "FR",
                "es": "ES",
                "it": "IT",
                "pt": "BR",
                "ru": "RU",
                "zh": "CN",
                "ja": "JP",
            }
            if language_code in language_map:
                return language_map[language_code]

        # Default to US if no matching country code is found
        return "US"

    @classmethod
    def _load_data(cls, country_code: str = "US") -> None:
        """Load data from CSV files.

        Args:
            country_code: The country code to load data for. Default is US.
        """
        if not cls._DATA_CACHE:
            # Set the data directory to the path where the medical data files are stored
            current_file = Path(__file__)
            data_dir = current_file.parent.parent / "data" / "medical"

            # Define categories of data to load with headers

            # Define categories of data to load without headers (simple lists)
            simple_categories = {
                "device_types": "device_types",
                "manufacturers": "manufacturers",
                "locations": "locations",
                "statuses": "device_statuses",
            }

            # Load each category of simple data
            for cache_key, file_prefix in simple_categories.items():
                # Try country-specific file first
                country_specific_path = data_dir / f"{file_prefix}_{country_code}.csv"
                if country_specific_path.exists():
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(country_specific_path)
                    continue

                # Try US as fallback
                fallback_path = data_dir / f"{file_prefix}_US.csv"
                if fallback_path.exists():
                    logger.info(f"Using US fallback for {file_prefix} data as {country_code} not available")
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(fallback_path)
                    continue

                # Last resort - try without country code
                generic_path = data_dir / f"{file_prefix}.csv"
                if generic_path.exists():
                    logger.warning(f"Using generic data for {file_prefix} - consider creating country-specific file")
                    cls._DATA_CACHE[cache_key] = cls._load_simple_csv(generic_path)

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file with one value per line.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file, with weighted values repeated according to their weight
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                result = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if the line contains a comma (indicating a weighted value)
                    if "," in line:
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            value = parts[0].strip()
                            try:
                                # Try to convert the weight to an integer
                                weight = int(parts[1].strip())
                                # Add the value to the result list 'weight' times
                                result.extend([value] * weight)
                                continue
                            except ValueError:
                                # If weight is not an integer, treat the whole line as a single value
                                pass

                    # If no comma or invalid weight, add the line as a single value
                    result.append(line)

                return result
        except Exception as e:
            logger.error(f"Error loading simple CSV file {file_path}: {e}")
            return []

    def _get_cached_property(self, property_name: str, generator_func: Callable[[], T]) -> T:
        """Get a cached property or generate and cache it if not present.

        Args:
            property_name: The name of the property to get.
            generator_func: The function to generate the property value.

        Returns:
            The cached or newly generated property value.
        """
        if property_name not in self._property_cache:
            self._property_cache[property_name] = generator_func()
        return cast(T, self._property_cache[property_name])

    def _generate_device_id(self) -> str:
        """Generate a unique device ID."""
        return f"DEV-{random.randint(10000000, 99999999)}"

    def _generate_device_type(self) -> str:
        """Generate a device type."""
        if self._device_type:
            return self._device_type

        device_types = self._DATA_CACHE.get("device_types", [])
        if not device_types:
            logger.warning("No device types found in data cache, using emergency default")
            return "Ventilator"
        return random.choice(device_types)

    def _generate_manufacturer(self) -> str:
        """Generate a manufacturer."""
        if self._manufacturer:
            return self._manufacturer

        manufacturers = self._DATA_CACHE.get("manufacturers", [])
        if not manufacturers:
            logger.warning("No manufacturers found in data cache, using emergency default")
            return "Medical Device Company"
        return random.choice(manufacturers)

    def _generate_model_number(self) -> str:
        """Generate a model number."""
        # Format: Letters followed by numbers and possibly more letters
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        prefix = "".join(random.choices(letters, k=random.randint(1, 3)))
        numbers = "".join(random.choices("0123456789", k=random.randint(3, 5)))
        suffix = "".join(random.choices(letters, k=random.randint(0, 2)))

        return f"{prefix}-{numbers}{suffix}"

    def _generate_serial_number(self) -> str:
        """Generate a serial number.
        
        Returns:
            A serial number in the format of 3 uppercase letters followed by 8 digits.
        """
        # Generate 3 uppercase letters
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        
        # Generate 8 digits
        digits = ''.join(random.choices(string.digits, k=8))
        
        return f"{letters}{digits}"

    def _generate_manufacture_date(self) -> str:
        """Generate a manufacture date."""
        # Generate a date between 1 and 10 years ago
        days_ago = random.randint(365, 3650)  # 1 to 10 years
        manufacture_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return manufacture_date.strftime("%Y-%m-%d")

    def _generate_expiration_date(self) -> str:
        """Generate an expiration date."""
        # Generate a date between 1 and 10 years after manufacture date
        manufacture_date = datetime.datetime.strptime(self.manufacture_date, "%Y-%m-%d")
        days_ahead = random.randint(365, 3650)  # 1 to 10 years
        expiration_date = manufacture_date + datetime.timedelta(days=days_ahead)
        return expiration_date.strftime("%Y-%m-%d")

    def _generate_last_maintenance_date(self) -> str:
        """Generate a last maintenance date."""
        # Generate a date between manufacture date and now
        manufacture_date = datetime.datetime.strptime(self.manufacture_date, "%Y-%m-%d")
        now = datetime.datetime.now()

        # Calculate days between manufacture date and now
        days_between = (now - manufacture_date).days

        # If device is very new, maintenance might be on the same day as manufacture
        if days_between <= 0:
            return self.manufacture_date

        # Otherwise, pick a random date between manufacture and now
        days_after_manufacture = random.randint(0, days_between)
        last_maintenance_date = manufacture_date + datetime.timedelta(days=days_after_manufacture)
        return last_maintenance_date.strftime("%Y-%m-%d")

    def _generate_next_maintenance_date(self) -> str:
        """Generate a next maintenance date."""
        # Generate a date between 1 day and 1 year after last maintenance date
        last_maintenance_date = datetime.datetime.strptime(self.last_maintenance_date, "%Y-%m-%d")
        days_ahead = random.randint(1, 365)  # 1 day to 1 year
        next_maintenance_date = last_maintenance_date + datetime.timedelta(days=days_ahead)
        return next_maintenance_date.strftime("%Y-%m-%d")

    def _generate_status(self) -> str:
        """Generate a status."""
        if self._status:
            return self._status

        statuses = self._DATA_CACHE.get("statuses", [])
        if not statuses:
            logger.warning("No statuses found in data cache, using emergency default")
            return "Active"
        return random.choice(statuses)

    def _generate_location(self) -> str:
        """Generate a location."""
        if self._location:
            return self._location

        locations = self._DATA_CACHE.get("locations", [])
        if not locations:
            logger.warning("No locations found in data cache, using emergency default")
            return "Hospital"
        return random.choice(locations)

    def _generate_assigned_to(self) -> str:
        """Generate an assigned to value."""
        # 30% chance of not being assigned to anyone
        if random.random() < 0.3:
            return ""

        # Otherwise, generate a person name
        if hasattr(self, "_person_entity"):
            return f"{self._person_entity.given_name} {self._person_entity.family_name}"

        # Fallback if person entity is not available
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_specifications(self) -> dict[str, str]:
        """Generate specifications."""
        # Generate specifications based on device type
        device_type = self.device_type

        # Common specifications for all devices
        specs = {
            "dimensions": f"{random.randint(10, 200)}x{random.randint(10, 200)}x{random.randint(5, 100)} cm",
            "weight": f"{random.randint(1, 500)} kg",
            "power_supply": random.choice(["AC", "Battery", "AC/Battery", "Solar", "Manual"]),
            "voltage": random.choice(["110V", "220V", "110-240V"]),
            "certification": random.choice(["FDA", "CE", "ISO", "UL", "CSA"]),
        }

        # Add device-specific specifications
        if "Ventilator" in device_type:
            specs.update(
                {
                    "flow_rate": f"{random.randint(1, 100)} L/min",
                    "pressure_range": f"{random.randint(1, 50)} cmH2O",
                    "modes": random.choice(["Volume Control", "Pressure Control", "SIMV", "CPAP", "BiPAP"]),
                }
            )
        elif "Monitor" in device_type:
            specs.update(
                {
                    "screen_size": f"{random.randint(10, 30)} inches",
                    "resolution": random.choice(["HD", "Full HD", "4K"]),
                    "parameters": random.choice(
                        ["ECG, SpO2, NIBP", "ECG, SpO2, NIBP, Temp", "ECG, SpO2, NIBP, Temp, CO2"]
                    ),
                }
            )
        elif "Pump" in device_type:
            specs.update(
                {
                    "flow_rate": f"{random.randint(1, 1000)} mL/hr",
                    "accuracy": f"±{random.randint(1, 5)}%",
                    "alarms": random.choice(
                        ["Air-in-Line, Occlusion, Door Open", "Air-in-Line, Occlusion, Door Open, Low Battery"]
                    ),
                }
            )
        elif "Scanner" in device_type or "Machine" in device_type:
            specs.update(
                {
                    "resolution": f"{random.randint(1, 10)} mm",
                    "scan_time": f"{random.randint(1, 60)} seconds",
                    "radiation_dose": f"{random.randint(1, 100)} mSv",
                }
            )

        return specs

    def _generate_usage_logs(self) -> list[dict[str, str]]:
        """Generate usage logs."""
        # Generate 0-5 usage logs
        num_logs = random.randint(0, 5)

        if num_logs == 0:
            return []

        logs = []

        # Generate usage logs
        manufacture_date = datetime.datetime.strptime(self.manufacture_date, "%Y-%m-%d")
        now = datetime.datetime.now()

        # Calculate days between manufacture date and now
        days_between = (now - manufacture_date).days

        # If device is very new, no usage logs
        if days_between <= 0:
            return []

        # Generate random dates for usage logs
        for _ in range(num_logs):
            days_after_manufacture = random.randint(0, days_between)
            log_date = manufacture_date + datetime.timedelta(days=days_after_manufacture)

            # Generate user
            if hasattr(self, "_person_entity"):
                self._person_entity.reset()
                user = f"{self._person_entity.given_name} {self._person_entity.family_name}"
            else:
                first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
                last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia"]
                user = f"{random.choice(first_names)} {random.choice(last_names)}"

            # Generate action
            actions = [
                "Powered On",
                "Powered Off",
                "Calibrated",
                "Used in Procedure",
                "Settings Changed",
                "Alarm Triggered",
            ]
            action = random.choice(actions)

            # Generate details
            details = ""
            if action == "Used in Procedure":
                procedures = ["Surgery", "Diagnosis", "Monitoring", "Treatment", "Therapy"]
                details = f"Used in {random.choice(procedures)} procedure"
            elif action == "Settings Changed":
                settings = ["Volume", "Pressure", "Flow Rate", "Temperature", "Alarm Thresholds"]
                details = f"Changed {random.choice(settings)} settings"
            elif action == "Alarm Triggered":
                alarms = ["Low Battery", "High Pressure", "Low Pressure", "Occlusion", "Air-in-Line", "Door Open"]
                details = f"{random.choice(alarms)} alarm triggered"

            logs.append(
                {
                    "date": log_date.strftime("%Y-%m-%d"),
                    "user": user,
                    "action": action,
                    "details": details,
                }
            )

        # Sort logs by date (most recent first)
        logs.sort(key=lambda x: datetime.datetime.strptime(cast(str, x["date"]), "%Y-%m-%d"), reverse=True)

        return logs

    def _generate_maintenance_history(self) -> list[dict[str, Any]]:
        """Generate maintenance history."""
        # Generate 0-3 maintenance records
        num_records = random.randint(0, 3)

        if num_records == 0:
            return []

        records = []

        # Generate maintenance records
        manufacture_date = datetime.datetime.strptime(self.manufacture_date, "%Y-%m-%d")
        last_maintenance_date = datetime.datetime.strptime(self.last_maintenance_date, "%Y-%m-%d")

        # Calculate days between manufacture date and last maintenance date
        days_between = (last_maintenance_date - manufacture_date).days

        # If device is very new or no maintenance has been done, no maintenance history
        if days_between <= 0:
            return []

        # Generate random dates for maintenance records
        for _ in range(num_records):
            days_after_manufacture = random.randint(0, days_between)
            record_date = manufacture_date + datetime.timedelta(days=days_after_manufacture)

            # Generate technician
            if hasattr(self, "_person_entity"):
                self._person_entity.reset()
                technician = f"{self._person_entity.given_name} {self._person_entity.family_name}"
            else:
                first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
                last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia"]
                technician = f"{random.choice(first_names)} {random.choice(last_names)}"

            # Generate actions
            maintenance_actions = [
                "Routine Inspection",
                "Calibration",
                "Software Update",
                "Hardware Repair",
                "Parts Replacement",
                "Cleaning",
                "Battery Replacement",
                "Preventive Maintenance",
            ]

            # Select 1-3 actions
            num_actions = random.randint(1, 3)
            actions = random.sample(maintenance_actions, min(num_actions, len(maintenance_actions)))

            # Generate notes
            notes_options = [
                "Device functioning properly",
                "Minor issues found and resolved",
                "Recommended for replacement within next year",
                "Software updated to latest version",
                "Calibration within acceptable range",
                "Parts showing signs of wear",
                "No issues found",
                "Scheduled for follow-up maintenance",
            ]
            notes = random.choice(notes_options)

            records.append(
                {
                    "date": record_date.strftime("%Y-%m-%d"),
                    "technician": technician,
                    "actions": actions,
                    "notes": notes,
                }
            )

        # Sort records by date (most recent first)
        records.sort(key=lambda x: datetime.datetime.strptime(cast(str, x["date"]), "%Y-%m-%d"), reverse=True)

        return records

    def reset(self) -> None:
        """Reset all field generators and caches."""
        for generator in self._field_generators.values():
            generator.reset()

        # Reset person entity if available
        if hasattr(self, "_person_entity"):
            self._person_entity.reset()

        # Clear property cache
        self._property_cache.clear()

    @property
    def device_id(self) -> str:
        """Get the device ID."""
        return cast(str, self._get_cached_property("device_id", lambda: self._field_generators["device_id"].get()))

    @property
    def device_type(self) -> str:
        """Get the device type."""
        return cast(str, self._get_cached_property("device_type", lambda: self._field_generators["device_type"].get()))

    @property
    def manufacturer(self) -> str:
        """Get the manufacturer."""
        return cast(
            str, self._get_cached_property("manufacturer", lambda: self._field_generators["manufacturer"].get())
        )

    @property
    def model_number(self) -> str:
        """Get the model number."""
        return cast(
            str, self._get_cached_property("model_number", lambda: self._field_generators["model_number"].get())
        )

    @property
    def serial_number(self) -> str:
        """Get the serial number."""
        return cast(
            str, self._get_cached_property("serial_number", lambda: self._field_generators["serial_number"].get())
        )

    @property
    def manufacture_date(self) -> str:
        """Get the manufacture date."""
        return cast(
            str, self._get_cached_property("manufacture_date", lambda: self._field_generators["manufacture_date"].get())
        )

    @property
    def expiration_date(self) -> str:
        """Get the expiration date."""
        return cast(
            str, self._get_cached_property("expiration_date", lambda: self._field_generators["expiration_date"].get())
        )

    @property
    def last_maintenance_date(self) -> str:
        """Get the last maintenance date."""
        return cast(
            str,
            self._get_cached_property(
                "last_maintenance_date", lambda: self._field_generators["last_maintenance_date"].get()
            ),
        )

    @property
    def next_maintenance_date(self) -> str:
        """Get the next maintenance date."""
        return cast(
            str,
            self._get_cached_property(
                "next_maintenance_date", lambda: self._field_generators["next_maintenance_date"].get()
            ),
        )

    @property
    def status(self) -> str:
        """Get the status."""
        return cast(str, self._get_cached_property("status", lambda: self._field_generators["status"].get()))

    @property
    def location(self) -> str:
        """Get the location."""
        return cast(str, self._get_cached_property("location", lambda: self._field_generators["location"].get()))

    @property
    def assigned_to(self) -> str:
        """Get the assigned to value."""
        return cast(str, self._get_cached_property("assigned_to", lambda: self._field_generators["assigned_to"].get()))

    @property
    def specifications(self) -> dict[str, str]:
        """Get the specifications."""
        return cast(
            dict[str, str],
            self._get_cached_property("specifications", lambda: self._field_generators["specifications"].get()),
        )

    @property
    def usage_logs(self) -> list[dict[str, str]]:
        """Get the usage logs."""
        return cast(
            list[dict[str, str]],
            self._get_cached_property("usage_logs", lambda: self._field_generators["usage_logs"].get()),
        )

    @property
    def maintenance_history(self) -> list[dict[str, Any]]:
        """Get the maintenance history."""
        return cast(
            list[dict[str, Any]],
            self._get_cached_property(
                "maintenance_history", lambda: self._field_generators["maintenance_history"].get()
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
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
        """Generate a batch of medical device data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated medical device data.
        """
        field_names = [
            "device_id",
            "device_type",
            "manufacturer",
            "model_number",
            "serial_number",
            "manufacture_date",
            "expiration_date",
            "last_maintenance_date",
            "next_maintenance_date",
            "status",
            "location",
            "assigned_to",
            "specifications",
            "usage_logs",
            "maintenance_history",
        ]

        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
