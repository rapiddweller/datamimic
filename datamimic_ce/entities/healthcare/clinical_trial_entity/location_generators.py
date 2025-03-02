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

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.healthcare.clinical_trial_entity.data_loader import ClinicalTrialDataLoader
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
    # Check if class_factory_util is provided
    if not class_factory_util:
        logger.error("No class_factory_util provided for location generation. Cannot create location.")
        return {"name": "", "address": "", "contact": {"phone": "", "email": ""}}

    try:
        # Create an address entity with the specified country code
        address_entity = AddressEntity(class_factory_util, country_code=country_code)

        # Get facility types from data loader
        data_loader = ClinicalTrialDataLoader()
        facility_options = data_loader.get_country_specific_data("facility_types", country_code)

        # If no facility types are found in data files, use a minimal set
        if not facility_options:
            logger.warning(f"No facility types found for {country_code}. Please create a data file.")
            if country_code == "DE":
                facility_type = "Medizinisches Zentrum"
            else:
                facility_type = "Medical Center"
        else:
            # Choose a facility type based on weights
            from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import weighted_choice

            facility_type = weighted_choice(facility_options)

        # Create facility name using address city
        facility = f"{facility_type} {address_entity.city}"

        # Format address as a string
        address = (
            f"{address_entity.city}, {address_entity.state} {address_entity.postal_code}, {address_entity.country}"
        )

        # Generate contact info based on facility name
        if country_code == "DE":
            email_domain = "de"
            phone_prefix = "+49"
        else:
            email_domain = "org"
            phone_prefix = "+1"

        # Generate phone number
        phone = f"{phone_prefix}-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

        # Generate email
        email = f"contact@{facility.lower().replace(' ', '')}.{email_domain}".replace(",", "").replace(".", "-")

        return {"name": facility, "address": address, "contact": {"phone": phone, "email": email}}
    except Exception as e:
        logger.error(f"Failed to generate location: {e}")
        return {"name": "", "address": "", "contact": {"phone": "", "email": ""}}


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
