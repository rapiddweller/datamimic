# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Participant generators for the Clinical Trial Entity.

This module provides functions for generating participant-related data for clinical trials.
"""

import random
from typing import cast

from datamimic_ce.entities.healthcare.clinical_trial_entity.data_loader import ClinicalTrialDataLoader
from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import weighted_choice
from datamimic_ce.logger import logger


def generate_enrollment_count(status: str, phase: str) -> int:
    """Generate a realistic enrollment count based on the trial status and phase.

    Args:
        status: The status of the trial
        phase: The phase of the trial

    Returns:
        An integer representing the enrollment count
    """
    # Define base enrollment ranges by phase
    phase_ranges = {
        "Early Phase 1": (5, 30),
        "Phase 1": (10, 50),
        "Phase 2": (50, 300),
        "Phase 3": (300, 3000),
        "Phase 4": (100, 1000),
        "Not Applicable": (20, 200),
    }

    # Get the base range for the phase, or use a default range
    base_min, base_max = phase_ranges.get(phase, (20, 200))

    # Adjust based on status
    if status.lower() == "completed":
        # Completed trials have their full enrollment
        return random.randint(base_min, base_max)
    elif status.lower() == "terminated":
        # Terminated trials typically have partial enrollment
        return random.randint(int(base_min * 0.1), int(base_max * 0.5))
    elif status.lower() == "withdrawn":
        # Withdrawn trials may have very few or no participants
        return random.randint(0, int(base_min * 0.5))
    elif status.lower() == "active, not recruiting":
        # Active but not recruiting trials have their full enrollment
        return random.randint(base_min, base_max)
    elif status.lower() == "recruiting":
        # Recruiting trials have partial enrollment
        return random.randint(int(base_min * 0.1), int(base_max * 0.8))
    elif status.lower() == "not yet recruiting":
        # Not yet recruiting trials have no enrollment
        return 0
    else:
        # Default case
        return random.randint(base_min, base_max)


def generate_eligibility_criteria(
    condition: str | None = None, data_loader: ClinicalTrialDataLoader | None = None, country_code: str = "US"
) -> dict[str, list[str]]:
    """Generate eligibility criteria for a clinical trial.

    Args:
        condition: Optional condition being studied
        data_loader: Optional data loader to use for retrieving criteria
        country_code: Country code (default: "US")

    Returns:
        A dictionary containing inclusion and exclusion criteria
    """
    inclusion_criteria = []
    exclusion_criteria = []

    # Try to use the data loader if provided
    if data_loader:
        try:
            # Get inclusion criteria from the data loader
            inclusion_data = data_loader.get_country_specific_data("inclusion_criteria", country_code)
            # Choose 3-6 inclusion criteria
            num_inclusion = random.randint(3, 6)
            for _ in range(num_inclusion):
                if inclusion_data:
                    criterion = weighted_choice(inclusion_data)
                    if criterion and criterion not in inclusion_criteria:
                        inclusion_criteria.append(criterion)

            # Get exclusion criteria from the data loader
            exclusion_data = data_loader.get_country_specific_data("exclusion_criteria", country_code)
            # Choose 3-6 exclusion criteria
            num_exclusion = random.randint(3, 6)
            for _ in range(num_exclusion):
                if exclusion_data:
                    criterion = weighted_choice(exclusion_data)
                    if criterion and criterion not in exclusion_criteria:
                        exclusion_criteria.append(criterion)
        except Exception as e:
            logger.warning(f"Failed to use data loader for eligibility criteria: {e}")
            # Fall through to the default criteria

    # If we couldn't get criteria from the data loader, use default criteria
    if not inclusion_criteria:
        inclusion_criteria = [
            "Age 18-65 years",
            "Diagnosis of the condition under study",
            "Able to provide informed consent",
            "Willing to comply with study procedures",
        ]
        # Add condition-specific criterion if condition is provided
        if condition:
            inclusion_criteria.append(f"Confirmed diagnosis of {condition}")

    if not exclusion_criteria:
        exclusion_criteria = [
            "Pregnancy or breastfeeding",
            "Serious medical condition that would interfere with the study",
            "Known hypersensitivity to study medication",
            "Participation in another clinical trial within 30 days",
        ]
        # Add condition-specific criterion if condition is provided
        if condition:
            exclusion_criteria.append(f"History of allergic reactions to treatments for {condition}")

    return {
        "inclusion": inclusion_criteria,
        "exclusion": exclusion_criteria,
    }


def generate_age_range(
    condition: str | None = None, data_loader: ClinicalTrialDataLoader | None = None
) -> dict[str, int | None]:
    """Generate a realistic age range for clinical trial participants.

    Args:
        condition: Optional condition being studied
        data_loader: Optional data loader to use for retrieving age range data

    Returns:
        A dictionary containing the minimum and maximum age
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            age_ranges_data = data_loader.get_country_specific_data("age_ranges", "US")
            if age_ranges_data:
                selected_range_str = weighted_choice(age_ranges_data)
                # Parse the string into a dictionary
                try:
                    # Example format: "18-65" or "18-None" for no upper limit
                    min_max = selected_range_str.split("-")
                    min_age = int(min_max[0])
                    max_age = None if min_max[1].lower() == "none" else int(min_max[1])
                    return {"min": min_age, "max": max_age}
                except (ValueError, IndexError):
                    logger.warning(f"Failed to parse age range: {selected_range_str}")
                    # Fall through to the default age ranges
        except Exception as e:
            logger.warning(f"Failed to use data loader for age ranges: {e}")
            # Fall through to the default age ranges

    # Define common age ranges for clinical trials with weights
    age_ranges = [
        ({"min": 18, "max": 65}, 50),  # Adult studies
        ({"min": 18, "max": None}, 20),  # Adult studies with no upper limit
        ({"min": 65, "max": None}, 10),  # Elderly studies
        ({"min": 12, "max": 17}, 5),  # Adolescent studies
        ({"min": 6, "max": 11}, 5),  # Child studies
        ({"min": 2, "max": 5}, 5),  # Young child studies
        ({"min": 0, "max": 1}, 5),  # Infant studies
    ]

    # Choose a random age range using direct random.choices instead of weighted_choice
    # to avoid type issues since we're dealing with dictionaries, not strings
    age_range_options = [age_range for age_range, _ in age_ranges]
    weights = [weight for _, weight in age_ranges]
    selected_range = cast(dict[str, int | None], random.choices(age_range_options, weights=weights, k=1)[0])

    # Ensure we're returning a dict[str, int | None]
    return selected_range


def generate_gender_eligibility(
    condition: str | None = None, data_loader: ClinicalTrialDataLoader | None = None
) -> str:
    """Generate gender eligibility for a clinical trial.

    Args:
        condition: Optional condition being studied
        data_loader: Optional data loader to use for retrieving gender eligibility data

    Returns:
        A string representing the gender eligibility
    """
    # Try to use the data loader if provided
    if data_loader:
        try:
            gender_options = data_loader.get_country_specific_data("gender_eligibility", "US")
            if gender_options:
                return weighted_choice(gender_options)
        except Exception as e:
            logger.warning(f"Failed to use data loader for gender eligibility: {e}")
            # Fall through to the default options

    # Define possible gender eligibility options
    gender_options = [("All", 80), ("Male", 10), ("Female", 10)]

    # Return a weighted choice
    return weighted_choice(gender_options)
