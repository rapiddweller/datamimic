# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# """
# Base entity class for all domain entities.

# This module provides a base class with common functionality for all domain entities.
# """

# from abc import ABC, abstractmethod
# from typing import Any, ClassVar, TypeVar

# T = TypeVar("T")  # Define a type variable for generic typing


from abc import ABC, abstractmethod
from typing import Any


class BaseEntity(ABC):
    def __init__(self):
        self._field_cache = {}

    @property
    def field_cache(self):
        return self._field_cache

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.") 
