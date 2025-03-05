"""
This module serves as a compatibility layer for the LabEntity class.
It imports the actual implementation from the healthcare.lab_test_entity module.
"""

from typing import Any, ClassVar

from datamimic_ce.entities.healthcare.lab_test_entity import LabTestEntity


# Add class-level cache for tests by creating a subclass
class LabEntityWithCache(LabTestEntity):
    """LabEntity with additional class cache for compatibility."""

    _DATA_CACHE: ClassVar[dict[str, Any]] = {}


# Replace the original LabEntity with our enhanced version
LabEntity = LabEntityWithCache

# Re-export the LabEntity class
__all__ = ["LabEntity"]
