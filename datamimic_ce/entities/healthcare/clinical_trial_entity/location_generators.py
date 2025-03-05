# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Location generators for the Clinical Trial Entity.

This module provides functions for generating location data for clinical trials.
"""

import random
from typing import Any

from datamimic_ce.logger import logger
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


def generate_single_location(
    country_code: str = "US", class_factory_util: BaseClassFactoryUtil | None = None
) -> dict[str, Any]:
    """Generate a single location for a clinical trial.

    Args:
        country_code: Country code (default: "US")
        class_factory_util: Optional class factory utility for creating entities

    Returns:
        A dictionary containing location details
    """
    # Try to use AddressEntity if available
    if class_factory_util:
        try:
            from datamimic_ce.entities.address_entity import AddressEntity

            # Create an address entity with the specified country code
            address_entity = AddressEntity(class_factory_util, country_code=country_code)

            # Return a dictionary with the location details
            facility_options = ["University", "Hospital", "Medical Center", "Clinic", "Research Institute"]
            facility = f"{random.choice(facility_options)} of {address_entity.city}"

            # Format address as a string
            address = (
                f"{address_entity.city}, {address_entity.state} {address_entity.postal_code}, {address_entity.country}"
            )

            # Generate random contact info
            phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            email = f"contact@{facility.lower().replace(' ', '')}.org".replace(",", "").replace(".", "-")

            return {"name": facility, "address": address, "contact": {"phone": phone, "email": email}}
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to use AddressEntity for location: {e}")
            # Fall through to the fallback method

    # Fallback to static generation if AddressEntity is not available
    if country_code == "US":
        cities = [
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
        ]
        states = [
            "MA",
            "NY",
            "IL",
            "CA",
            "TX",
            "PA",
            "AZ",
            "TX",
            "CA",
            "TX",
        ]
        city_index = random.randint(0, len(cities) - 1)
        facility_options = ["University", "Hospital", "Medical Center", "Clinic", "Research Institute"]
        facility = f"{random.choice(facility_options)} of {cities[city_index]}"

        # Format address
        zip_code = f"{random.randint(10000, 99999)}"
        address = f"{cities[city_index]}, {states[city_index]} {zip_code}, United States"

        # Generate random contact info
        phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        email = f"contact@{facility.lower().replace(' ', '')}.org".replace(",", "").replace(".", "-")

        return {"name": facility, "address": address, "contact": {"phone": phone, "email": email}}
    elif country_code == "DE":
        cities = [
            "Berlin",
            "Hamburg",
            "Munich",
            "Cologne",
            "Frankfurt",
            "Stuttgart",
            "Düsseldorf",
            "Leipzig",
            "Dortmund",
            "Essen",
        ]
        states = [
            "Berlin",
            "Hamburg",
            "Bavaria",
            "North Rhine-Westphalia",
            "Hesse",
            "Baden-Württemberg",
            "North Rhine-Westphalia",
            "Saxony",
            "North Rhine-Westphalia",
            "North Rhine-Westphalia",
        ]
        city_index = random.randint(0, len(cities) - 1)
        facility_options = [
            "Universitätsklinikum",
            "Krankenhaus",
            "Medizinisches Zentrum",
            "Klinik",
            "Forschungsinstitut",
        ]
        facility = f"{random.choice(facility_options)} {cities[city_index]}"

        # Format address
        zip_code = f"{random.randint(10000, 99999)}"
        address = f"{cities[city_index]}, {states[city_index]} {zip_code}, Germany"

        # Generate random contact info
        phone = f"+49-{random.randint(100, 999)}-{random.randint(1000000, 9999999)}"
        email = f"kontakt@{facility.lower().replace(' ', '')}.de".replace(",", "").replace(".", "-")

        return {"name": facility, "address": address, "contact": {"phone": phone, "email": email}}
    else:
        # Generic location for other countries
        facility = f"Medical Center {random.randint(1, 100)}"
        city = f"City {random.randint(1, 100)}"
        state = f"State {random.randint(1, 50)}"
        zip_code = f"{random.randint(10000, 99999)}"

        # Format address
        address = f"{city}, {state} {zip_code}, {country_code}"

        # Generate random contact info
        phone = f"+xx-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        email = f"contact@{facility.lower().replace(' ', '')}.com".replace(",", "").replace(".", "-")

        return {"name": facility, "address": address, "contact": {"phone": phone, "email": email}}


def generate_locations(
    num_locations: int = 1,
    country_codes: list[str] | None = None,
    class_factory_util: BaseClassFactoryUtil | None = None,
) -> list[dict[str, Any]]:
    """Generate multiple locations for a clinical trial.

    Args:
        num_locations: Number of locations to generate
        country_codes: List of country codes to use (default: ["US"])
        class_factory_util: Optional class factory utility for creating entities

    Returns:
        A list of dictionaries containing location details
    """
    # Default to US if no country codes are provided
    if not country_codes:
        country_codes = ["US"]

    locations = []
    for _ in range(num_locations):
        # Choose a random country code from the list
        country_code = random.choice(country_codes)
        # Generate a location for the chosen country
        location = generate_single_location(country_code, class_factory_util)
        locations.append(location)

    return locations


def determine_num_locations(phase: str, status: str) -> int:
    """Determine a realistic number of locations based on the trial phase and status.

    Args:
        phase: The phase of the trial
        status: The status of the trial

    Returns:
        An integer representing the number of locations
    """
    # Define base location ranges by phase
    phase_ranges = {
        "Early Phase 1": (1, 3),
        "Phase 1": (1, 5),
        "Phase 2": (3, 15),
        "Phase 3": (10, 50),
        "Phase 4": (5, 30),
        "Not Applicable": (1, 10),
    }

    # Get the base range for the phase, or use a default range
    base_min, base_max = phase_ranges.get(phase, (1, 10))

    # Adjust based on status
    if status.lower() in ["completed", "active, not recruiting"]:
        # Completed or active trials have their full number of locations
        return random.randint(base_min, base_max)
    elif status.lower() == "recruiting":
        # Recruiting trials might have slightly fewer locations
        return random.randint(base_min, int(base_max * 0.8))
    elif status.lower() == "not yet recruiting":
        # Not yet recruiting trials might have even fewer locations
        return random.randint(base_min, int(base_max * 0.5))
    elif status.lower() in ["terminated", "withdrawn"]:
        # Terminated or withdrawn trials typically have fewer locations
        return random.randint(1, int(base_max * 0.3))
    else:
        # Default case
        return random.randint(base_min, base_max)
