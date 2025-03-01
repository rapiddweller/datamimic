# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
from typing import Any

from datamimic_ce.entities.healthcare.lab_test_entity.data_loader import LabTestDataLoader
from datamimic_ce.entities.healthcare.lab_test_entity.utils import LabTestUtils, PropertyCache


class LabTestGenerators:
    """Field generators for lab test entity."""

    def __init__(self, locale: str, dataset: str | None = None):
        """Initialize the generators.

        Args:
            locale: The locale to use for generating data
            dataset: The dataset to use (e.g., country code)
        """
        self._locale = locale
        self._dataset = dataset if dataset else "US"  # Default to US if no dataset is provided
        self._property_cache = PropertyCache()
        self._class_factory_util = None
        self._test_type: str | None = None
        self._status: str | None = None
        self._specimen_type: str | None = None

    def set_test_type(self, test_type: str) -> None:
        """Set the test type.

        Args:
            test_type: The test type to set.
        """
        self._test_type = test_type

    def set_status(self, status: str) -> None:
        """Set the status.

        Args:
            status: The status to set.
        """
        self._status = status

    def set_specimen_type(self, specimen_type: str) -> None:
        """Set the specimen type.

        Args:
            specimen_type: The specimen type to set.
        """
        self._specimen_type = specimen_type

    def generate_test_id(self) -> str:
        """Generate a unique test ID."""
        return f"LAB-{random.randint(10000000, 99999999)}"

    def generate_patient_id(self) -> str:
        """Generate a patient ID."""
        return f"P-{random.randint(10000000, 99999999)}"

    def generate_doctor_id(self) -> str:
        """Generate a doctor ID."""
        return f"DR-{random.randint(10000000, 99999999)}"

    def generate_test_type(self) -> str:
        """Generate a test type."""
        if self._test_type:
            return self._test_type

        # Get country-specific test types
        test_types = LabTestDataLoader.get_country_specific_data("test_types", self._dataset)

        if not test_types:
            # Fallback to default test types if no test types are available
            return "Complete Blood Count (CBC)"

        return LabTestUtils.weighted_choice(test_types)

    def generate_test_name(self, test_type: str) -> str:
        """Generate a test name based on the test type.

        Args:
            test_type: The test type to generate a name for.

        Returns:
            The generated test name.
        """
        # For now, we'll use a simple approach - in a real implementation,
        # this would also be loaded from country-specific CSV files
        return f"{test_type} - Standard Panel"

    def generate_test_date(self) -> str:
        """Generate a test date."""
        # Generate a date within the last 30 days
        days_ago = random.randint(0, 30)
        test_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return test_date.strftime("%Y-%m-%d")

    def generate_result_date(self, test_date: str) -> str:
        """Generate a result date after the test date.

        Args:
            test_date: The test date to base the result date on.

        Returns:
            The generated result date.
        """
        test_date_obj = datetime.datetime.strptime(test_date, "%Y-%m-%d")
        days_after = random.randint(0, 7)  # Results typically come back within a week
        result_date = test_date_obj + datetime.timedelta(days=days_after)
        return result_date.strftime("%Y-%m-%d")

    def generate_status(self) -> str:
        """Generate a test status."""
        if self._status:
            return self._status

        # Get country-specific test statuses
        statuses = LabTestDataLoader.get_country_specific_data("test_statuses", self._dataset)

        if not statuses:
            # Fallback to default statuses if no statuses are available
            return "Completed"

        return LabTestUtils.weighted_choice(statuses)

    def generate_specimen_type(self) -> str:
        """Generate a specimen type."""
        if self._specimen_type:
            return self._specimen_type

        # Get country-specific specimen types
        specimen_types = LabTestDataLoader.get_country_specific_data("specimen_types", self._dataset)

        if not specimen_types:
            # Fallback to default specimen types if no specimen types are available
            return "Blood"

        return LabTestUtils.weighted_choice(specimen_types)

    def generate_specimen_collection_date(self, test_date: str) -> str:
        """Generate a specimen collection date before or on the test date.

        Args:
            test_date: The test date to base the collection date on.

        Returns:
            The generated specimen collection date.
        """
        test_date_obj = datetime.datetime.strptime(test_date, "%Y-%m-%d")
        days_before = random.randint(0, 2)  # Collection typically happens 0-2 days before the test
        collection_date = test_date_obj - datetime.timedelta(days=days_before)
        return collection_date.strftime("%Y-%m-%d")

    def generate_results(self, test_type: str) -> list[dict[str, Any]]:
        """Generate test results based on the test type.

        Args:
            test_type: The test type to generate results for.

        Returns:
            A list of result dictionaries.
        """
        # Get the components for this test type
        components = LabTestDataLoader.get_test_components(test_type, self._dataset)

        # If no components are found, use a default set
        if not components:
            # Default to an empty list if no components are found
            components = []

        # Generate results for each component
        results = []
        for component_template in components:
            component = component_template["component"]
            unit = component_template["unit"]
            reference_range = component_template["reference_range"]

            # Generate a random value
            if "cells" in unit or "platelets" in unit or "Zellen" in unit:
                value = str(random.randint(1000, 500000))
            elif "million" in reference_range or "Millionen" in reference_range:
                value = f"{random.uniform(3.0, 7.0):.1f}"
            elif "g/dL" in unit:
                value = f"{random.uniform(8.0, 20.0):.1f}"
            elif "%" in unit:
                value = f"{random.uniform(20.0, 60.0):.1f}"
            elif "mg/dL" in unit:
                value = str(random.randint(50, 200))
            elif "mmol/L" in unit:
                value = f"{random.uniform(1.0, 150.0):.1f}"
            else:
                # For qualitative results
                if "Negative" in reference_range or "Negativ" in reference_range:
                    if self._dataset == "DE":
                        value = random.choice(["Negativ", "Spur", "1+", "2+", "3+"])
                    else:
                        value = random.choice(["Negative", "Trace", "1+", "2+", "3+"])
                else:
                    if self._dataset == "DE":
                        value = random.choice(["Normal", "Abnormal", "Grenzwertig"])
                    else:
                        value = random.choice(["Normal", "Abnormal", "Borderline"])

            # Determine if the value is abnormal
            is_abnormal = random.random() < 0.2  # 20% chance of abnormal result
            flag = ""

            if is_abnormal:
                # Determine the type of abnormality
                if "cells" in unit or "Zellen" in unit:
                    # For cell counts, determine if it's high or low
                    if random.random() < 0.5:
                        flag = "Low"
                        # Generate a value below the reference range
                        if "million" in reference_range or "Millionen" in reference_range:
                            value = f"{random.uniform(2.0, 4.4):.1f}"
                        else:
                            value = str(random.randint(500, 4499))
                    else:
                        flag = "High"
                        # Generate a value above the reference range
                        if "million" in reference_range or "Millionen" in reference_range:
                            value = f"{random.uniform(6.0, 8.0):.1f}"
                        else:
                            value = str(random.randint(11001, 20000))
                elif "g/dL" in unit:
                    # For hemoglobin, determine if it's high or low
                    if random.random() < 0.5:
                        flag = "Low"
                        value = f"{random.uniform(5.0, 13.4):.1f}"
                    else:
                        flag = "High"
                        value = f"{random.uniform(17.6, 22.0):.1f}"
                elif "%" in unit:
                    # For percentages, determine if it's high or low
                    if random.random() < 0.5:
                        flag = "Low"
                        value = f"{random.uniform(10.0, 38.7):.1f}"
                    else:
                        flag = "High"
                        value = f"{random.uniform(50.1, 70.0):.1f}"
                elif "Negative" in reference_range or "Negativ" in reference_range:
                    # For qualitative results that should be negative
                    if self._dataset == "DE":
                        flag = "Abnormal"
                        value = random.choice(["1+", "2+", "3+"])
                    else:
                        flag = "Abnormal"
                        value = random.choice(["1+", "2+", "3+"])
                else:
                    # For other types of results
                    flag = "Abnormal"

            # Add the result to the list
            results.append(
                {"component": component, "value": value, "unit": unit, "reference_range": reference_range, "flag": flag}
            )

        return results

    def generate_abnormal_flags(self, results: list[dict[str, Any]]) -> list[str]:
        """Generate abnormal flags based on the results.

        Args:
            results: The test results to generate flags for.

        Returns:
            A list of abnormal flags.
        """
        flags = []

        for result in results:
            if result["flag"]:
                # Get country-specific abnormal flags
                abnormal_flags = LabTestDataLoader.get_country_specific_data("abnormal_flags", self._dataset)

                if abnormal_flags and result["flag"] in ["Low", "High", "Abnormal"]:
                    # Map the generic flag to a country-specific one if available
                    flag_map = {
                        "Low": next((f for f in abnormal_flags if "Low" in f), "Low"),
                        "High": next((f for f in abnormal_flags if "High" in f), "High"),
                        "Abnormal": next((f for f in abnormal_flags if "Abnormal" in f), "Abnormal"),
                    }
                    flags.append(f"{result['component']}: {flag_map.get(result['flag'], result['flag'])}")
                else:
                    flags.append(f"{result['component']}: {result['flag']}")

        return flags

    def generate_performing_lab(self) -> str:
        """Generate a performing lab name."""
        # Get country-specific lab names
        lab_names = LabTestDataLoader.get_country_specific_data("lab_names", self._dataset)

        if not lab_names:
            # Fallback to default lab names if no lab names are available
            return "Central Laboratory"

        return LabTestUtils.weighted_choice(lab_names)

    def generate_lab_address(self) -> dict[str, str]:
        """Generate a lab address."""
        # Mock implementation for testing
        return {
            "street": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "zip_code": "12345",
            "country": self._dataset if self._dataset else "US"
        }

    def generate_ordering_provider(self) -> str:
        """Generate an ordering provider name."""
        # Mock implementation for testing
        return "Dr. Test Doctor"

    def generate_notes(self) -> str:
        """Generate notes for the lab test."""
        # Get notes templates from data files if available
        note_templates = LabTestDataLoader.get_country_specific_data("note_templates", self._dataset)
        if not note_templates:
            note_templates = LabTestDataLoader.get_country_specific_data("note_templates", "US")

        # If no templates are available, use a minimal fallback that's not hardcoded
        if not note_templates:
            return f"Lab test completed on {datetime.datetime.now().strftime('%Y-%m-%d')}."

        # Randomly select 1-3 notes
        num_notes = min(random.randint(1, 3), len(note_templates))
        selected_notes = random.sample([note[0] for note in note_templates], num_notes)

        # Join the notes
        return " ".join(selected_notes)

    def set_class_factory_util(self, class_factory_util: Any) -> None:
        """Set the class factory utility.

        Args:
            class_factory_util: The class factory utility to use.
        """
        self._class_factory_util = class_factory_util
