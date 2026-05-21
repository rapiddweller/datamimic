# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime as dt
from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice

MEDICAL_DEVICE_SCHEMA = EntitySchema(
    "MedicalDevice",
    (
        field("device_id", str, "Unique device identifier."),
        field("device_type", str, "Device type."),
        field("manufacturer", str, "Manufacturer name."),
        field("model_number", str, "Model number."),
        field("serial_number", str, "Serial number."),
        field("manufacture_date", str, "Manufacture date."),
        field("expiration_date", str, "Expiration date."),
        field("last_maintenance_date", str, "Date of last maintenance."),
        field("next_maintenance_date", str, "Date of next scheduled maintenance."),
        field("status", str, "Device status."),
        field("location", str, "Device location."),
        field("assigned_to", str, "Person or unit the device is assigned to."),
        field("specifications", dict, "Technical specifications."),
        field("usage_logs", list, "Usage log entries."),
        field("maintenance_history", list, "Maintenance history entries."),
    ),
)


class MedicalDeviceService(BaseDomainService[MedicalDevice]):
    """Service for managing medical device data.

    This class provides methods to create, retrieve, and manage medical device data.
    It integrates the model, data loader, and generator components.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        rng: Random | None = None,
        reference_now: dt.datetime | None = None,
    ):
        """Initialize the MedicalDeviceService.

        Args:
            dataset: The dataset to use for generating medical device data.
            demographic_config: Optional demographic configuration.
            rng: Optional seeded random instance for deterministic output.
            reference_now: Optional fixed datetime to use as "now".
        """
        super().__init__(
            MedicalDeviceGenerator(
                dataset=dataset,
                demographic_config=demographic_config,
                rng=rng,
                reference_now=reference_now,
            ),
            MedicalDevice,
        )

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return MEDICAL_DEVICE_SCHEMA.fields

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "healthcare/medical/device_types_{CC}.csv",
            "healthcare/medical/manufacturers_{CC}.csv",
            "healthcare/medical/device_statuses_{CC}.csv",
            "healthcare/medical/locations_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
