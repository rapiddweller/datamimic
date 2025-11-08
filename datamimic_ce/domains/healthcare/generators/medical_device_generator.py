# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.domains.common.models.demographic_config import DemographicConfig

import datetime
import random
from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class MedicalDeviceGenerator(BaseDomainGenerator):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        demographic_config: DemographicConfig | None = None,
    ):
        self._dataset = (dataset or "US").upper()  #  normalize once so we always map to _{dataset}.csv inputs
        self._rng: random.Random = rng or random.Random()
        #  thread demographic constraints to person details used in usage logs/technicians
        if demographic_config is None:
            from datamimic_ce.domains.common.models.demographic_config import DemographicConfig as _DC

            demographic_config = _DC()
        self._person_generator = PersonGenerator(
            dataset=self._dataset, demographic_config=demographic_config, rng=self._rng
        )
        self._last_manufacturer: str | None = None

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    # Date helpers to keep model pure and deterministic
    def generate_manufacture_date(self) -> str:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now - datetime.timedelta(days=3650)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(dt, datetime.datetime)
        return dt.strftime("%Y-%m-%d")

    def generate_expiration_date(self) -> str:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now + datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = (now + datetime.timedelta(days=1825)).strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(dt, datetime.datetime)
        return dt.strftime("%Y-%m-%d")

    def generate_last_maintenance_date(self) -> str:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now - datetime.timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(dt, datetime.datetime)
        return dt.strftime("%Y-%m-%d")

    def generate_next_maintenance_date(self) -> str:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = (now + datetime.timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(dt, datetime.datetime)
        return dt.strftime("%Y-%m-%d")

    def generate_device_type(self) -> str:
        file_path = dataset_path("healthcare", "medical", f"device_types_{self._dataset}.csv", start=Path(__file__))
        loaded_data = FileUtil.read_weight_csv(file_path)
        values: list[str] = [str(v) for v in loaded_data[0].tolist() if v is not None]
        weights: list[float] = [float(w) for w in loaded_data[1].tolist()]
        return self._rng.choices(values, weights=weights, k=1)[0]

    def generate_manufacturer(self) -> str:
        file_path = dataset_path("healthcare", "medical", f"manufacturers_{self._dataset}.csv", start=Path(__file__))
        loaded_data = FileUtil.read_weight_csv(file_path)
        values: list[str] = [str(v) for v in loaded_data[0].tolist() if v is not None]
        weights: list[float] = [float(w) for w in loaded_data[1].tolist()]
        # avoid immediate repetition when possible
        if self._last_manufacturer in values and len(values) > 1:
            pool = [(v, float(w)) for v, w in zip(values, weights, strict=False) if v != self._last_manufacturer]
            p_vals, p_w = zip(*pool, strict=False)
            choice = self._rng.choices(list(p_vals), weights=list(p_w), k=1)[0]
        else:
            choice = self._rng.choices(values, weights=weights, k=1)[0]
        self._last_manufacturer = choice
        return choice

    def generate_device_status(self) -> str:
        file_path = dataset_path("healthcare", "medical", f"device_statuses_{self._dataset}.csv", start=Path(__file__))
        loaded_data = FileUtil.read_weight_csv(file_path)
        values: list[str] = [str(v) for v in loaded_data[0].tolist() if v is not None]
        weights: list[float] = [float(w) for w in loaded_data[1].tolist()]
        return self._rng.choices(values, weights=weights, k=1)[0]

    def generate_location(self) -> str:
        file_path = dataset_path("healthcare", "medical", f"locations_{self._dataset}.csv", start=Path(__file__))
        loaded_data = FileUtil.read_weight_csv(file_path)
        values: list[str] = [str(v) for v in loaded_data[0].tolist() if v is not None]
        weights: list[float] = [float(w) for w in loaded_data[1].tolist()]
        return self._rng.choices(values, weights=weights, k=1)[0]

    # Helpers for specifications (modes, detector types, etc.) used by the model
    def pick_ventilator_mode(self) -> str:
        values, w = load_weighted_values_try_dataset(
            "healthcare", "medical", "ventilator_modes.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, w)

    def pick_mri_field_strength(self) -> str:
        values, w = load_weighted_values_try_dataset(
            "healthcare", "medical", "mri_field_strengths.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, w)

    def pick_xray_detector_type(self) -> str:
        values, w = load_weighted_values_try_dataset(
            "healthcare", "medical", "xray_detector_types.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, w)

    def pick_ultrasound_probe_type(self) -> str:
        values, w = load_weighted_values_try_dataset(
            "healthcare", "medical", "ultrasound_probe_types.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, w)

    def pick_ultrasound_imaging_mode(self) -> str:
        values, w = load_weighted_values_try_dataset(
            "healthcare", "medical", "ultrasound_imaging_modes.csv", dataset=self._dataset, start=Path(__file__)
        )
        return pick_one_weighted(self._rng, values, w)

    def generate_usage_log(self, username: str, device_type: str) -> list[dict[str, str]]:
        logs = []

        # Generate between 3 and 10 usage logs
        num_logs = self._rng.randint(3, 10)

        # Start date for logs (between 1 and 2 years ago)
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now - datetime.timedelta(days=730)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        current_date = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(current_date, datetime.datetime)

        for _ in range(num_logs):
            # Move forward in time for each log
            days_forward = self._rng.randint(5, 60)
            current_date += datetime.timedelta(days=days_forward)

            # Skip if we've gone past today
            if current_date > datetime.datetime.now():
                break

            # Generate a log entry
            log_entry = {
                "date": current_date.strftime("%Y-%m-%d"),
                "user": username,
                "duration_minutes": str(self._rng.randint(15, 240)),
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
        from pathlib import Path

        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        dtype = device_type.lower()
        # Base purposes
        base_path = dataset_path("healthcare", "medical", f"usage_purposes_{self._dataset}.csv", start=Path(__file__))
        base_vals, base_w = FileUtil.read_wgt_file(base_path)
        # Device-specific purposes (optional)
        specific_vals: list[str] = []
        specific_w: list[float] = []
        if any(k in dtype for k in ("ventilator", "mri", "x-ray", "ultrasound")):
            key = (
                "xray"
                if "x-ray" in dtype
                else ("mri" if "mri" in dtype else ("ultrasound" if "ultrasound" in dtype else "ventilator"))
            )
            spec_path = dataset_path(
                "healthcare",
                "medical",
                f"usage_purposes_{key}_{self._dataset}.csv",
                start=Path(__file__),
            )
            try:
                specific_vals, specific_w = FileUtil.read_wgt_file(spec_path)
            except FileNotFoundError:
                specific_vals, specific_w = [], []  #  device-specific overrides are optional per dataset
        values = base_vals + specific_vals
        weights = base_w + specific_w
        return self._rng.choices(values, weights=weights, k=1)[0]

    def _generate_usage_notes(self) -> str:
        """Generate notes for device usage.

        Returns:
            A string representing usage notes.
        """
        from pathlib import Path

        from datamimic_ce.domains.utils.dataset_path import dataset_path
        from datamimic_ce.utils.file_util import FileUtil

        path = dataset_path("healthcare", "medical", f"usage_notes_{self._dataset}.csv", start=Path(__file__))
        values, weights = FileUtil.read_wgt_file(path)

        # 20% chance of no notes
        if self._rng.random() < 0.2:
            return ""
        return self._rng.choices(values, weights=weights, k=1)[0]

    def generate_maintenance_history(self) -> list[dict[str, Any]]:
        """Generate maintenance history for the device.

        Returns:
            A list of dictionaries representing maintenance history.
        """
        history = []

        # Generate between 2 and 8 maintenance records
        num_records = self._rng.randint(2, 8)

        # Start date for maintenance (between 1 and 3 years ago)
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = (now - datetime.timedelta(days=1095)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        current_date = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(current_date, datetime.datetime)

        for _ in range(num_records):
            # Move forward in time for each maintenance
            days_forward = self._rng.randint(30, 180)
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
                "duration_hours": round(self._rng.uniform(0.5, 8.0), 1),
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
        # Use the existing PersonGenerator for realistic technician names
        from datamimic_ce.domains.common.models.person import Person

        person = Person(self._person_generator)
        return f"{person.given_name} {person.family_name}"

    def _generate_maintenance_type(self) -> str:
        """Generate a maintenance type.

        Returns:
            A string representing a maintenance type.
        """
        path = dataset_path("healthcare", "medical", f"maintenance_types_{self._dataset}.csv", start=Path(__file__))
        values, w = FileUtil.read_wgt_file(path)
        return self._rng.choices(values, weights=w, k=1)[0]

    def _generate_parts_replaced(self) -> list[str]:
        """Generate a list of parts replaced during maintenance.

        Returns:
            A list of strings representing parts replaced.
        """
        path = dataset_path("healthcare", "medical", f"maintenance_parts_{self._dataset}.csv", start=Path(__file__))
        values, _ = FileUtil.read_wgt_file(path)

        # 40% chance of no parts replaced
        if self._rng.random() < 0.4:
            return []

        # Otherwise, replace 1-3 parts
        num_parts = self._rng.randint(1, 3)
        # random.sample doesn't support custom RNG; emulate sampling without replacement
        pool = list(values)
        chosen: list[str] = []
        for _ in range(min(num_parts, len(pool))):
            idx = self._rng.randrange(len(pool))
            chosen.append(pool.pop(idx))
        return chosen

    def _generate_maintenance_cost(self) -> float:
        """Generate a maintenance cost.

        Returns:
            A float representing a maintenance cost.
        """
        # Base cost between $100 and $500
        base_cost = self._rng.uniform(100, 500)

        # If parts were replaced, add more cost
        if self._rng.random() < 0.6:  # 60% chance of parts replacement
            parts_cost = self._rng.uniform(200, 2000)
            return round(base_cost + parts_cost, 2)

        return round(base_cost, 2)

    def _generate_maintenance_result(self) -> str:
        """Generate a maintenance result.

        Returns:
            A string representing a maintenance result.
        """
        #  remove hardcoded values; source from dataset for localization and consistency
        path = dataset_path("healthcare", "medical", f"maintenance_results_{self._dataset}.csv", start=Path(__file__))
        values, w = FileUtil.read_wgt_file(path)
        return self._rng.choices(values, weights=w, k=1)[0]

    def _generate_maintenance_notes(self) -> str:
        """Generate notes for maintenance history.

        Returns:
            A string representing maintenance notes.
        """
        #  remove hardcoded values; source from dataset for localization and consistency
        path = dataset_path("healthcare", "medical", f"maintenance_notes_{self._dataset}.csv", start=Path(__file__))
        values, w = FileUtil.read_wgt_file(path)

        # 10% chance of no notes
        if self._rng.random() < 0.1:
            return ""
        return self._rng.choices(values, weights=w, k=1)[0]

    def _derive_rng(self) -> random.Random:
        # Fork deterministic child RNGs so seeded medical device descriptors replay without cross-coupling draws.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()
