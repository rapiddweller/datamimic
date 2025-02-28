# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
This module serves as a compatibility layer for the LabTestEntity class.
It imports the actual implementation from the lab_test_entity package.
"""

import random
from pathlib import Path

# Import the actual implementation from the package
from datamimic_ce.entities.healthcare.lab_test_entity.core import LabTestEntity as LabTestEntityImpl
from datamimic_ce.entities.healthcare.lab_test_entity.data_loader import LabTestDataLoader
from datamimic_ce.entities.healthcare.lab_test_entity.utils import LabTestUtils
from datamimic_ce.logger import logger


# For backward compatibility
class LabTestEntity(LabTestEntityImpl):
    """Generate laboratory test data.

    This class generates realistic laboratory test data including test IDs,
    patient IDs, doctor IDs, test types, test names, dates, statuses,
    specimen types, results, abnormal flags, performing labs, lab addresses,
    ordering providers, and notes.

    This is a compatibility wrapper around the actual implementation in the lab_test_entity package.
    """

    # Module-level cache for data to reduce file I/O (for backward compatibility)
    _DATA_CACHE: dict[str, list[str]] = {}
    # Module-level cache for component data (for backward compatibility)
    _COMPONENT_CACHE: dict[str, list[dict[str, str]]] = {}
    # Module-level cache for dictionary data (for backward compatibility)
    _DICT_CACHE: dict[str, dict[str, str]] = {}

    @staticmethod
    def _load_simple_csv(file_path: Path) -> list[str]:
        """Load a simple CSV file and return a list of values.

        This is a compatibility method that delegates to LabTestDataLoader.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of values from the CSV file
        """
        # Call the actual implementation but convert the result to the expected format
        result = LabTestDataLoader._load_simple_csv(file_path)
        # Convert list of tuples to list of strings for backward compatibility
        return [f"{value},{weight}" if weight != 1.0 else value for value, weight in result]

    @classmethod
    def _get_country_specific_data(cls, data_type: str, country_code: str = "US") -> list[str]:
        """Get country-specific data from CSV files.

        This is a compatibility method that delegates to LabTestDataLoader.

        Args:
            data_type: Type of data to retrieve (e.g., "labs", "providers")
            country_code: Country code (default: "US")

        Returns:
            List of values from the CSV file
        """
        result = LabTestDataLoader.get_country_specific_data(data_type, country_code)
        return [item[0] for item in result]  # Extract just the values, not the weights

    @classmethod
    def _get_test_component_mapping(cls) -> dict[str, str]:
        """Get mapping of test types to component files.

        This is a compatibility method that delegates to LabTestDataLoader.

        Returns:
            Dictionary mapping test types to component file names
        """
        return LabTestDataLoader.get_test_component_mapping()

    @classmethod
    def _get_test_components(cls, test_type: str, country_code: str = "US") -> list[dict[str, str]]:
        """Get components for a specific test type.

        This is a compatibility method that delegates to LabTestDataLoader.

        Args:
            test_type: Type of test
            country_code: Country code (default: "US")

        Returns:
            List of component dictionaries
        """
        return LabTestDataLoader.get_test_components(test_type, country_code)

    @staticmethod
    def _weighted_choice(values: list[str]) -> str:
        """Choose a value from a list based on weights.

        This is a compatibility method that delegates to LabTestUtils.

        Args:
            values: List of values, potentially with weights

        Returns:
            A chosen value
        """
        return LabTestUtils.weighted_choice(values)

    @staticmethod
    def _parse_weighted_value(value: str) -> tuple[str, float]:
        """Parse a weighted value from a CSV file.

        This is a compatibility method that delegates to LabTestUtils.

        Args:
            value: The value to parse

        Returns:
            A tuple of (value, weight)
        """
        return LabTestUtils.parse_weighted_value(value)

    # Override properties to ensure they never return empty values by forcing regeneration
    @property
    def test_type(self) -> str:
        """Get the test type."""
        value = super().test_type
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().test_type
        return value

    @property
    def status(self) -> str:
        """Get the status."""
        value = super().status
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().status
        return value

    @property
    def specimen_type(self) -> str:
        """Get the specimen type."""
        value = super().specimen_type
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().specimen_type
        return value

    @property
    def performing_lab(self) -> str:
        """Get the performing lab."""
        value = super().performing_lab
        if not value:
            # Force regeneration by clearing the cache for this property
            self._property_cache.clear()
            return super().performing_lab
        return value

    def _generate_lab_address(self) -> dict[str, str]:
        """Generate a lab address."""
        # Use AddressEntity if available
        if self._class_factory_util:
            try:
                from datamimic_ce.entities.address_entity import AddressEntity

                # Create an address entity with the same locale/country code
                address_entity = AddressEntity(
                    self._class_factory_util, locale=self._locale, country_code=self._country_code
                )

                # Return a dictionary with the address components
                return {
                    "street": f"{address_entity.house_number} {address_entity.street}",
                    "city": address_entity.city,
                    "state": address_entity.state,
                    "zip_code": address_entity.postal_code,
                    "country": address_entity.country,
                }
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to use AddressEntity for lab address: {e}")
                # Fall through to the fallback method

        # Fallback to static generation if AddressEntity is not available
        # Get lab names from data cache or use fallback
        lab_names = self._DATA_CACHE.get("lab_names", [])
        if lab_names:
            # If we have lab names, use them to generate more realistic addresses
            lab_name = self._weighted_choice(lab_names)

            # Get country-specific data if available
            streets = self._DATA_CACHE.get(
                "street_names",
                ["Medical Center Dr", "Laboratory Ave", "Healthcare Blvd", "Diagnostic Way", "Clinical Path"],
            )

            cities = self._DATA_CACHE.get(
                "cities",
                [
                    "Boston",
                    "New York",
                    "Chicago",
                    "Los Angeles",
                    "Houston",
                    "Philadelphia",
                    "Phoenix",
                    "San Antonio",
                    "San Diego",
                    "Dallas",
                ],
            )

            states = self._DATA_CACHE.get("states", ["MA", "NY", "IL", "CA", "TX", "PA", "AZ", "TX", "CA", "TX"])

            # Generate a random address
            street_name = self._weighted_choice(streets) if streets else "Medical Center Dr"
            city = self._weighted_choice(cities) if cities else "Boston"
            state = self._weighted_choice(states) if states else "MA"

            # Use the lab name in the street address for more realism
            return {
                "street": f"{random.randint(100, 9999)} {street_name}",
                "city": city,
                "state": state,
                "zip_code": f"{random.randint(10000, 99999)}",
                "country": "USA" if self._country_code == "US" else self._country_code,
            }
        else:
            # Simple fallback with generic values
            return {
                "street": f"{random.randint(100, 9999)} Medical Center Dr",
                "city": "Boston",
                "state": "MA",
                "zip_code": f"{random.randint(10000, 99999)}",
                "country": "USA" if self._country_code == "US" else self._country_code,
            }

    def _generate_ordering_provider(self) -> str:
        """Generate an ordering provider name."""
        # Use PersonEntity if available
        if self._class_factory_util:
            try:
                from datamimic_ce.entities.person_entity import PersonEntity

                # Create a person entity with the same locale/country code
                person_entity = PersonEntity(self._class_factory_util, locale=self._locale, dataset=self._dataset)

                # Generate a doctor name with credentials
                first_name = person_entity.given_name
                last_name = person_entity.family_name

                credentials = ["MD", "DO", "NP", "PA", "MBBS"]
                credential = random.choice(credentials)

                return f"Dr. {first_name} {last_name}, {credential}"
            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to use PersonEntity for ordering provider: {e}")
                # Fall through to the fallback method

        # Fallback to data-driven generation if PersonEntity is not available
        # Get provider names from data cache or use fallback
        provider_names = self._DATA_CACHE.get("provider_names", [])
        if provider_names:
            # If we have provider names, use them directly
            return self._weighted_choice(provider_names)

        # Final fallback to static generation
        # Get first and last names from data cache or use fallback
        first_names = self._DATA_CACHE.get(
            "first_names",
            [
                "James",
                "John",
                "Robert",
                "Michael",
                "William",
                "David",
                "Richard",
                "Joseph",
                "Thomas",
                "Charles",
                "Mary",
                "Patricia",
                "Jennifer",
                "Linda",
                "Elizabeth",
                "Barbara",
                "Susan",
                "Jessica",
                "Sarah",
                "Karen",
            ],
        )

        last_names = self._DATA_CACHE.get(
            "last_names",
            [
                "Smith",
                "Johnson",
                "Williams",
                "Jones",
                "Brown",
                "Davis",
                "Miller",
                "Wilson",
                "Moore",
                "Taylor",
                "Anderson",
                "Thomas",
                "Jackson",
                "White",
                "Harris",
                "Martin",
                "Thompson",
                "Garcia",
                "Martinez",
                "Robinson",
            ],
        )

        credentials = ["MD", "DO", "NP", "PA", "MBBS"]

        first_name = self._weighted_choice(first_names) if first_names else "John"
        last_name = self._weighted_choice(last_names) if last_names else "Smith"
        credential = random.choice(credentials)

        return f"Dr. {first_name} {last_name}, {credential}"
