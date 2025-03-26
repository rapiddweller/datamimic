# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from abc import ABC, abstractmethod
from typing import Any

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator


class BaseEntity(ABC):
    """
    Base class for all domain entities.

    This class provides common functionality for all entity objects used in domain models,
    including property access and validation.
    """

    def __init__(self, generator: BaseDomainGenerator | None = None):
        # Cache for generated values
        self._field_cache: dict[str, Any] = {}
        # self._generator = generator

    @property
    def field_cache(self):
        return self._field_cache

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.")
