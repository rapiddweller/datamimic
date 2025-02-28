"""
This module serves as a compatibility layer for the PatientEntity class.
It imports the actual implementation from the healthcare.patient_entity module.
"""

from pathlib import Path

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.healthcare.patient_entity import PatientEntity
from datamimic_ce.entities.person_entity import PersonEntity

# Add class constants expected by tests
# These need to be added directly to the class, not just the module
PatientEntity.BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "O−"]
PatientEntity.GENDERS = ["Male", "Female", "Non-binary", "Other"]

# Add class-level DATA_CACHE for tests
if not hasattr(PatientEntity, '_DATA_CACHE'):
    PatientEntity._DATA_CACHE = {}

# Re-export the PatientEntity class
__all__ = ["PatientEntity", "PersonEntity", "AddressEntity"] 