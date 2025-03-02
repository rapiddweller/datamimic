# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
from typing import Any

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.healthcare.lab_test_entity.data_loader import LabTestDataLoader
from datamimic_ce.entities.healthcare.lab_test_entity.utils import LabTestUtils, PropertyCache
from datamimic_ce.entities.person_entity import PersonEntity
from datamimic_ce.logger import logger


class LabTestGenerators:
    """Field generators for lab test entity."""

    # Constants for ID prefixes and formats
    LAB_TEST_ID_PREFIX = "LAB-"
    PATIENT_ID_PREFIX = "P-"
    DOCTOR_ID_PREFIX = "DR-"
    ID_MIN = 10000000
    ID_MAX = 99999999

    # Constants for date formats
    DATE_FORMAT = "%Y-%m-%d"

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
        self._person_entity = None
        self._address_entity = None
        self._doctor_entity = None

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

    def _initialize_entities(self) -> None:
        """Initialize the person and address entities if they haven't been initialized yet.

        This method ensures that the necessary entities are created only once and
        only when they are needed. It handles the case when class_factory_util is None.
        """
        if self._class_factory_util is None:
            return

        if self._person_entity is None:
            self._person_entity = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)

        if self._address_entity is None:
            # Convert None to empty string for dataset to satisfy type checker
            address_dataset = self._dataset if self._dataset is not None else ""
            self._address_entity = AddressEntity(self._class_factory_util, dataset=address_dataset, locale=self._locale)

    def generate_test_id(self) -> str:
        """Generate a unique test ID."""
        return f"{self.LAB_TEST_ID_PREFIX}{random.randint(self.ID_MIN, self.ID_MAX)}"

    def generate_patient_id(self) -> str:
        """Generate a patient ID.

        This method generates a patient ID in the same format as PatientEntity.
        """
        # Format consistent with PatientEntity._generate_patient_id
        return f"{self.PATIENT_ID_PREFIX}{random.randint(self.ID_MIN, self.ID_MAX)}"

    def generate_doctor_id(self) -> str:
        """Generate a doctor ID.

        This method generates a doctor ID in the same format as DoctorGenerators.
        """
        # Format consistent with DoctorGenerators.generate_doctor_id
        return f"{self.DOCTOR_ID_PREFIX}{random.randint(self.ID_MIN, self.ID_MAX)}"

    def generate_test_type(self) -> str:
        """Generate a test type."""
        if self._test_type:
            return self._test_type

        # Get country-specific test types
        test_types = LabTestDataLoader.get_country_specific_data("test_types", self._dataset)

        if not test_types:
            # Log error if no test types are available
            logger.error(f"No test types found for {self._dataset}. Please create a data file.")
            return "Unknown Test Type"

        return LabTestUtils.weighted_choice(test_types)

    def generate_test_name(self, test_type: str) -> str:
        """Generate a test name based on the test type.

        Args:
            test_type: The test type to generate a name for.

        Returns:
            The generated test name.
        """
        # Get country-specific test name templates
        test_name_templates = LabTestDataLoader.get_country_specific_data("test_name_templates", self._dataset)

        if test_name_templates:
            # Choose a template based on weights
            template = LabTestUtils.weighted_choice(test_name_templates)
            # Replace placeholder with test type
            return template.replace("{test_type}", test_type)

        # Log error if no templates are available
        logger.error(f"No test name templates found for {self._dataset}. Please create a data file.")
        return f"{test_type} Panel"

    def generate_test_date(self) -> str:
        """Generate a test date."""
        # Generate a date within the last 30 days
        days_ago = random.randint(0, 30)
        test_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return test_date.strftime(self.DATE_FORMAT)

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
            # Log error if no statuses are available
            logger.error(f"No test statuses found for {self._dataset}. Please create a data file.")
            return "Unknown Status"

        return LabTestUtils.weighted_choice(statuses)

    def generate_specimen_type(self) -> str:
        """Generate a specimen type."""
        if self._specimen_type:
            return self._specimen_type

        # Get country-specific specimen types
        specimen_types = LabTestDataLoader.get_country_specific_data("specimen_types", self._dataset)

        if not specimen_types:
            # Log error if no specimen types are available
            logger.error(f"No specimen types found for {self._dataset}. Please create a data file.")
            return "Unknown Specimen"

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

        # If no components are found, log an error
        if not components:
            logger.error(f"No test components found for {test_type} in {self._dataset}. Please create a data file.")
            return []

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
                    flag = "Abnormal"
                    value = random.choice(["1+", "2+", "3+"])

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
            # Use the address entity to generate a lab name
            self._initialize_entities()
            if self._address_entity:
                city = self._address_entity.city
                return f"{city} Medical Laboratory"

            # Log error if no lab names are available and no address entity
            logger.error(f"No lab names found for {self._dataset}. Please create a data file.")
            return "Unknown Laboratory"

        return LabTestUtils.weighted_choice(lab_names)

    def generate_lab_address(self) -> dict[str, str]:
        """Generate a lab address using AddressEntity."""
        self._initialize_entities()

        if self._address_entity:
            return {
                "street": f"{self._address_entity.street} {self._address_entity.house_number}",
                "city": self._address_entity.city,
                "state": self._address_entity.state,
                "zip_code": self._address_entity.postal_code,
                "country": self._address_entity.country,
            }

        # Log error if address entity is not available
        logger.error("Address entity not available. Please ensure AddressEntity is properly configured.")
        return self._generate_minimal_address()

    def _generate_minimal_address(self) -> dict[str, str]:
        """Generate a minimal address when AddressEntity is not available.

        Returns:
            A dictionary containing minimal address components.
        """
        # Get country-specific data if available
        streets = LabTestDataLoader.get_country_specific_data("streets", self._dataset)
        cities = LabTestDataLoader.get_country_specific_data("cities", self._dataset)
        states = LabTestDataLoader.get_country_specific_data("states", self._dataset)

        # Log errors if data is not available
        if not streets:
            logger.error(f"No streets found for {self._dataset}. Please create a data file.")
        if not cities:
            logger.error(f"No cities found for {self._dataset}. Please create a data file.")
        if not states:
            logger.error(f"No states found for {self._dataset}. Please create a data file.")

        # Use the data if available, otherwise use empty strings
        street = LabTestUtils.weighted_choice(streets) if streets else ""
        city = LabTestUtils.weighted_choice(cities) if cities else ""
        state = LabTestUtils.weighted_choice(states) if states else ""

        # Generate a house number and zip code
        house_number = str(random.randint(1, 999))
        zip_code = str(random.randint(10000, 99999))

        return {
            "street": f"{house_number} {street}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": self._dataset if self._dataset else "US",
        }

    def generate_ordering_provider(self) -> str:
        """Generate an ordering provider name using PersonEntity."""
        self._initialize_entities()

        if self._person_entity:
            # Create a doctor name with appropriate title
            title = self._get_doctor_title_for_locale(self._locale)
            return f"{title} {self._person_entity.given_name} {self._person_entity.family_name}"

        # Log error if person entity is not available
        logger.error("Person entity not available. Please ensure PersonEntity is properly configured.")
        return "Unknown Provider"

    def _get_doctor_title_for_locale(self, locale: str) -> str:
        """Get the appropriate doctor title for the given locale.

        Args:
            locale: The locale to get the title for.

        Returns:
            The appropriate doctor title for the locale.
        """
        # Map of locales to doctor titles
        locale_title_map = {
            "de": "Dr. med.",
            "fr": "Dr.",
            "es": "Dr.",
            "it": "Dott.",
            "nl": "Dr.",
            "pt": "Dr.",
            "ru": "Д-р",
            "ja": "医師",
            "zh": "医生",
        }

        # Extract language code from locale if it contains country code
        language_code = locale.split("_")[0].split("-")[0].lower() if locale else ""

        # Return the title for the locale if available, otherwise default to "Dr."
        return locale_title_map.get(language_code, "Dr.")

    def generate_notes(self) -> str:
        """Generate notes for the lab test."""
        self._initialize_entities()

        # Get notes templates from data files if available
        note_templates = LabTestDataLoader.get_country_specific_data("note_templates", self._dataset)
        if not note_templates:
            note_templates = LabTestDataLoader.get_country_specific_data("note_templates", "US")

        # If no templates are available, log an error
        if not note_templates:
            logger.error(f"No note templates found for {self._dataset}. Please create a data file.")
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            return f"Lab test completed on {current_date}."

        # Randomly select 1-3 notes
        num_notes = min(random.randint(1, 3), len(note_templates))
        selected_templates = random.sample([note[0] for note in note_templates], num_notes)

        # Replace placeholders in templates if person entity is available
        if self._person_entity:
            doctor_name = f"Dr. {self._person_entity.family_name}"
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")

            processed_notes = []
            for template in selected_templates:
                note = template.replace("{doctor}", doctor_name)
                note = note.replace("{date}", current_date)
                processed_notes.append(note)

            return " ".join(processed_notes)

        # Join the notes without replacements if no person entity
        return " ".join(selected_templates)

    def set_class_factory_util(self, class_factory_util: Any) -> None:
        """Set the class factory utility.

        Args:
            class_factory_util: The class factory utility to use.
        """
        self._class_factory_util = class_factory_util
        self._initialize_entities()
