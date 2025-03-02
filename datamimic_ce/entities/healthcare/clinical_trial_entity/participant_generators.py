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
from typing import Any

from datamimic_ce.entities.healthcare.clinical_trial_entity.data_loader import ClinicalTrialDataLoader
from datamimic_ce.entities.healthcare.clinical_trial_entity.utils import weighted_choice
from datamimic_ce.entities.healthcare.patient_entity import PatientEntity
from datamimic_ce.logger import logger
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


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
            # Log error but don't use fallbacks

    # If we couldn't get criteria from the data loader, log an error
    if not inclusion_criteria:
        logger.error(f"No inclusion criteria found for {country_code}. Please create a data file.")
        # Add condition-specific criterion if condition is provided
        if condition:
            inclusion_criteria.append(f"Confirmed diagnosis of {condition}")

    if not exclusion_criteria:
        logger.error(f"No exclusion criteria found for {country_code}. Please create a data file.")
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
        except Exception as e:
            logger.warning(f"Failed to use data loader for age ranges: {e}")

    # Log error if no data is available
    logger.error("No age ranges found in data files. Please create a data file.")
    # Return a default adult age range
    return {"min": 18, "max": 65}


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

    # Log error if no data is available
    logger.error("No gender eligibility options found in data files. Please create a data file.")
    # Return "All" as a safe default
    return "All"


def generate_participant_demographics(
    count: int,
    age_range: dict[str, int | None],
    gender_eligibility: str,
    class_factory_util: BaseClassFactoryUtil | None = None,
    country_code: str = "US",
) -> list[dict[str, Any]]:
    """Generate demographic information for a set of participants.

    Args:
        count: Number of participants to generate
        age_range: Age range for participants
        gender_eligibility: Gender eligibility criteria
        class_factory_util: Optional class factory utility for creating entities
        country_code: Country code (default: "US")

    Returns:
        A list of dictionaries containing participant demographics
    """
    if not class_factory_util:
        logger.error("No class_factory_util provided for participant generation.")
        return []

    participants = []
    min_age = age_range.get("min", 18)
    max_age = age_range.get("max", 65)

    for _ in range(count):
        try:
            # Create a patient entity for this participant
            patient = PatientEntity(class_factory_util, dataset=country_code)

            # Check if the patient meets the gender eligibility criteria
            if gender_eligibility != "All" and patient.gender.lower() != gender_eligibility.lower():
                # If gender doesn't match, create a new patient until we get one that matches
                attempts = 0
                while patient.gender.lower() != gender_eligibility.lower() and attempts < 5:
                    patient = PatientEntity(class_factory_util, dataset=country_code)
                    attempts += 1

                if patient.gender.lower() != gender_eligibility.lower():
                    # If we still don't have a match after 5 attempts, skip this participant
                    continue

            # Add the participant to the list
            participants.append(
                {
                    "id": patient.patient_id,
                    "age": random.randint(min_age, max_age or 80),
                    "gender": patient.gender,
                    "medical_history": patient.medical_history,
                    "allergies": patient.allergies,
                    "medications": patient.medications,
                }
            )

        except Exception as e:
            logger.error(f"Failed to generate participant: {e}")

    return participants
