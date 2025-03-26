# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
from pathlib import Path
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.utils.file_util import FileUtil


class MedicalDeviceGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._person_generator = PersonGenerator(dataset=self._dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    def generate_device_type(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"device_types_{self._dataset}.csv"
        )
        loaded_data = FileUtil.read_weight_csv(file_path)
        return random.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore[arg-type]

    def generate_manufacturer(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"manufacturers_{self._dataset}.csv"
        )
        loaded_data = FileUtil.read_weight_csv(file_path)
        return random.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore[arg-type]

    def generate_device_status(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"device_statuses_{self._dataset}.csv"
        )
        loaded_data = FileUtil.read_weight_csv(file_path)
        return random.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore[arg-type]

    def generate_location(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "healthcare"
            / "medical"
            / f"locations_{self._dataset}.csv"
        )
        loaded_data = FileUtil.read_weight_csv(file_path)  # type: ignore[arg-type]
        return random.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore[arg-type]

    def generate_usage_log(self, username: str, device_type: str) -> list[dict[str, str]]:
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
                "user": username,
                "duration_minutes": str(random.randint(15, 240)),
                "purpose": self._generate_usage_purpose(device_type),
                "notes": self._generate_usage_notes(),
            }

            logs.append(log_entry)

        return logs

    def _generate_usage_purpose(self, device_type: str) -> str:
        """Generate a purpose for device usage.

        Returns:
            A string representing a usage purpose.
        """
        device_type = device_type.lower()

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

    def generate_maintenance_history(self) -> list[dict[str, Any]]:
        """Generate maintenance history for the device.

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
        given_names = ["Alex", "Sam", "Jordan", "Casey", "Taylor", "Morgan", "Riley", "Jamie"]
        family_names = ["Tech", "Service", "Repair", "Maintenance", "Support", "Systems", "Engineering"]

        return f"{random.choice(given_names)} {random.choice(family_names)}"

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
