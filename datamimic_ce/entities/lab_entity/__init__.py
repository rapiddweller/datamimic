"""
This module serves as a compatibility layer for the LabEntity class.
It imports the actual implementation from the healthcare.lab_test_entity module.
"""

from datamimic_ce.entities.healthcare.lab_test_entity import LabTestEntity as LabEntity

# Add class-level cache for tests
LabEntity._DATA_CACHE = {}

# Re-export the LabEntity class
__all__ = ["LabEntity"] 