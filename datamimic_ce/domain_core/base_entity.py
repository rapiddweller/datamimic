# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from abc import ABC, abstractmethod
from typing import Any


class BaseEntity(ABC):
    """
    Base class for all domain entities.
    """
    def __init__(self):
        # Cache for generated values
        self._field_cache = {}

    @property
    def field_cache(self):
        return self._field_cache
        
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.") 
