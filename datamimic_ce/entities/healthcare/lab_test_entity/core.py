# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.entities.healthcare.lab_test_entity.generators import LabTestGenerators
from datamimic_ce.entities.healthcare.lab_test_entity.utils import PropertyCache


class LabTestEntity(Entity):
    """Generate laboratory test data.

    This class generates realistic laboratory test data including test IDs,
    patient IDs, doctor IDs, test types, test names, dates, statuses,
    specimen types, results, abnormal flags, performing labs, lab addresses,
    ordering providers, and notes.
    """

    def __init__(self, class_factory_util=None, locale: str = "en", dataset: str | None = None, **kwargs):
        """Initialize the LabTestEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._locale = locale  # Store the exact locale passed in
        self._dataset = dataset  # Store the dataset for country-specific data

        # Get optional parameters
        self._test_type = kwargs.get("test_type")
        self._status = kwargs.get("status")
        self._specimen_type = kwargs.get("specimen_type")

        # Initialize generators
        self._generators = LabTestGenerators(locale, dataset)

        # Set optional parameters in generators
        if self._test_type:
            self._generators.set_test_type(self._test_type)
        if self._status:
            self._generators.set_status(self._status)
        if self._specimen_type:
            self._generators.set_specimen_type(self._specimen_type)

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "test_id": self._generate_test_id,
                "patient_id": self._generate_patient_id,
                "doctor_id": self._generate_doctor_id,
                "test_type": self._generate_test_type,
                "test_name": self._generate_test_name,
                "test_date": self._generate_test_date,
                "result_date": self._generate_result_date,
                "status": self._generate_status,
                "specimen_type": self._generate_specimen_type,
                "specimen_collection_date": self._generate_specimen_collection_date,
                "results": self._generate_results,
                "abnormal_flags": self._generate_abnormal_flags,
                "performing_lab": self._generate_performing_lab,
                "lab_address": self._generate_lab_address,
                "ordering_provider": self._generate_ordering_provider,
                "notes": self._generate_notes,
            }
        )

        # Cache for entity properties
        self._property_cache = PropertyCache()

    def _generate_test_id(self) -> str:
        """Generate a unique test ID."""
        return self._generators.generate_test_id()

    def _generate_patient_id(self) -> str:
        """Generate a patient ID."""
        return self._generators.generate_patient_id()

    def _generate_doctor_id(self) -> str:
        """Generate a doctor ID."""
        return self._generators.generate_doctor_id()

    def _generate_test_type(self) -> str:
        """Generate a test type."""
        return self._generators.generate_test_type()

    def _generate_test_name(self) -> str:
        """Generate a test name based on the test type."""
        return self._generators.generate_test_name(self.test_type)

    def _generate_test_date(self) -> str:
        """Generate a test date."""
        return self._generators.generate_test_date()

    def _generate_result_date(self) -> str:
        """Generate a result date after the test date."""
        return self._generators.generate_result_date(self.test_date)

    def _generate_status(self) -> str:
        """Generate a status."""
        return self._generators.generate_status()

    def _generate_specimen_type(self) -> str:
        """Generate a specimen type."""
        return self._generators.generate_specimen_type()

    def _generate_specimen_collection_date(self) -> str:
        """Generate a specimen collection date before or on the test date."""
        return self._generators.generate_specimen_collection_date(self.test_date)

    def _generate_results(self) -> list[dict[str, Any]]:
        """Generate test results based on the test type."""
        return self._generators.generate_results(self.test_type)

    def _generate_abnormal_flags(self) -> list[str]:
        """Generate abnormal flags based on the results."""
        return self._generators.generate_abnormal_flags(self.results)

    def _generate_performing_lab(self) -> str:
        """Generate a performing lab name."""
        return self._generators.generate_performing_lab()

    def _generate_lab_address(self) -> dict[str, str]:
        """Generate a lab address."""
        return self._generators.generate_lab_address()

    def _generate_ordering_provider(self) -> str:
        """Generate an ordering provider name."""
        return self._generators.generate_ordering_provider()

    def _generate_notes(self) -> str:
        """Generate notes for the lab test."""
        return self._generators.generate_notes()

    def reset(self) -> None:
        """Reset the entity by clearing the property cache."""
        self._property_cache.clear()

    @property
    def test_id(self) -> str:
        """Get the test ID."""
        return self._property_cache.get("test_id", self._generate_test_id)

    @property
    def patient_id(self) -> str:
        """Get the patient ID."""
        return self._property_cache.get("patient_id", self._generate_patient_id)

    @property
    def doctor_id(self) -> str:
        """Get the doctor ID."""
        return self._property_cache.get("doctor_id", self._generate_doctor_id)

    @property
    def test_type(self) -> str:
        """Get the test type."""
        return self._property_cache.get("test_type", self._generate_test_type)

    @property
    def test_name(self) -> str:
        """Get the test name."""
        return self._property_cache.get("test_name", self._generate_test_name)

    @property
    def test_date(self) -> str:
        """Get the test date."""
        return self._property_cache.get("test_date", self._generate_test_date)

    @property
    def result_date(self) -> str:
        """Get the result date."""
        return self._property_cache.get("result_date", self._generate_result_date)

    @property
    def status(self) -> str:
        """Get the status."""
        return self._property_cache.get("status", self._generate_status)

    @property
    def specimen_type(self) -> str:
        """Get the specimen type."""
        return self._property_cache.get("specimen_type", self._generate_specimen_type)

    @property
    def specimen_collection_date(self) -> str:
        """Get the specimen collection date."""
        return self._property_cache.get("specimen_collection_date", self._generate_specimen_collection_date)

    @property
    def results(self) -> list[dict[str, Any]]:
        """Get the results."""
        return self._property_cache.get("results", self._generate_results)

    @property
    def abnormal_flags(self) -> list[str]:
        """Get the abnormal flags."""
        return self._property_cache.get("abnormal_flags", self._generate_abnormal_flags)

    @property
    def performing_lab(self) -> str:
        """Get the performing lab."""
        return self._property_cache.get("performing_lab", self._generate_performing_lab)

    @property
    def lab_address(self) -> dict[str, str]:
        """Get the lab address."""
        return self._property_cache.get("lab_address", self._generate_lab_address)

    @property
    def ordering_provider(self) -> str:
        """Get the ordering provider."""
        return self._property_cache.get("ordering_provider", self._generate_ordering_provider)

    @property
    def notes(self) -> str:
        """Get the notes."""
        return self._property_cache.get("notes", self._generate_notes)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary representation of the entity.
        """
        return {
            "test_id": self.test_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "test_type": self.test_type,
            "test_name": self.test_name,
            "test_date": self.test_date,
            "result_date": self.result_date,
            "status": self.status,
            "specimen_type": self.specimen_type,
            "specimen_collection_date": self.specimen_collection_date,
            "results": self.results,
            "abnormal_flags": self.abnormal_flags,
            "performing_lab": self.performing_lab,
            "lab_address": self.lab_address,
            "ordering_provider": self.ordering_provider,
            "notes": self.notes,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of lab test data.

        Args:
            count: The number of lab tests to generate.

        Returns:
            A list of dictionaries, each representing a lab test.
        """
        batch = []
        for _ in range(count):
            # Create a new instance for each item in the batch
            lab_test = LabTestEntity(
                self._class_factory_util,
                locale=self._locale if self._locale is not None else "en",
                dataset=self._dataset,
            )
            batch.append(lab_test.to_dict())
        return batch
