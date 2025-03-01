"""
This module serves as a compatibility layer for the PatientEntity class.
It imports the actual implementation from the healthcare.patient_entity module.
"""

# Remove unused Path import
from typing import Any, ClassVar

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.healthcare.patient_entity import PatientEntity as OriginalPatientEntity
from datamimic_ce.entities.person_entity import PersonEntity


# Add class constants expected by tests by modifying the class
# We need to use a different approach since direct attribute assignment is not working
class PatientEntityWithConstants(OriginalPatientEntity):
    """PatientEntity with additional class constants for compatibility."""

    # Include both hyphen and Unicode minus sign versions to handle both cases
    BLOOD_TYPES: ClassVar[list[str]] = ["A+", "A-", "A−", "B+", "B-", "B−", "AB+", "AB-", "AB−", "O+", "O-", "O−"]
    GENDERS: ClassVar[list[str]] = ["Male", "Female", "Non-binary", "Other"]
    # Use a different name to avoid conflict with the instance variable
    _CLASS_DATA_CACHE: ClassVar[dict[str, Any]] = {}


# Replace the original PatientEntity with our enhanced version
PatientEntity = PatientEntityWithConstants

# Re-export the PatientEntity class
__all__ = ["PatientEntity", "PersonEntity", "AddressEntity"]
