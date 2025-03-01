# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Base healthcare entity class.

This module provides a base class for all healthcare entities with common functionality.
"""

from abc import abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.property_cache import PropertyCache
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil

T = TypeVar("T")


class HealthcareEntity(Entity):
    """Base class for all healthcare entities.

    This class provides common functionality for healthcare entities, including
    property caching, country code determination, and utility methods.
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil | None = None,
        locale: str = "en",
        country_code: str = "US",
        dataset: str | None = None,
    ) -> None:
        """Initialize a new HealthcareEntity.

        Args:
            class_factory_util: Utility for creating related entities
            locale: Locale code for generating localized data
            country_code: Country code for location-specific data
            dataset: Optional dataset name for consistent data generation
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._country_code = self._determine_country_code(dataset, locale, country_code)

        # Initialize property cache
        self._property_cache: PropertyCache = PropertyCache()

        # Initialize data loader - to be implemented by subclasses
        self._initialize_data_loader()

    @abstractmethod
    def _initialize_data_loader(self) -> None:
        """Initialize the data loader for this entity.

        This method should be implemented by subclasses to initialize
        their specific data loader.
        """
        pass

    def _determine_country_code(self, dataset: str | None, locale: str, default_country_code: str) -> str:
        """Determine the country code to use based on dataset and locale.

        Args:
            dataset: The dataset parameter
            locale: The locale parameter
            default_country_code: The default country code to use if none can be determined

        Returns:
            A two-letter country code
        """
        # If dataset is provided and it's a valid country code, prioritize it
        if dataset and len(dataset) == 2:
            return dataset.upper()

        # Try to extract country code from locale
        if locale:
            # Check for formats like "en_US" or "de-DE"
            if "_" in locale and len(locale.split("_")) > 1:
                country_part = locale.split("_")[1]
                if len(country_part) == 2:
                    return country_part.upper()
            elif "-" in locale and len(locale.split("-")) > 1:
                country_part = locale.split("-")[1]
                if len(country_part) == 2:
                    return country_part.upper()

            # Direct matching for 2-letter codes
            if len(locale) == 2:
                return locale.upper()

            # Map common language codes to countries
            language_code = locale.split("_")[0].split("-")[0].lower()
            language_map = {
                "en": "US",
                "de": "DE",
                "fr": "FR",
                "es": "ES",
                "it": "IT",
                "pt": "BR",
                "ru": "RU",
                "zh": "CN",
                "ja": "JP",
            }
            if language_code in language_map:
                return language_map[language_code]

        # Default to the provided default country code
        return default_country_code

    def reset(self) -> None:
        """Reset the entity's cache."""
        self._property_cache.clear()

    def get_cached_property(self, property_name: str, generator_func: Callable[[], T]) -> T:
        """Get a cached property value or generate it if not in cache.

        Args:
            property_name: The name of the property
            generator_func: The function to generate the property value

        Returns:
            The property value
        """
        return self._property_cache.get_or_create(property_name, generator_func)

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary representation of the entity
        """
        pass

    @classmethod
    def generate_batch(
        cls,
        count: int,
        class_factory_util: BaseClassFactoryUtil | None = None,
        locale: str = "en",
        country_code: str = "US",
        dataset: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a batch of entities.

        Args:
            count: Number of entities to generate
            class_factory_util: Utility for creating related entities
            locale: Locale code for generating localized data
            country_code: Country code for location-specific data
            dataset: Optional dataset name for consistent data generation

        Returns:
            A list of dictionaries representing the generated entities
        """
        entities = []
        for _ in range(count):
            entity = cls(class_factory_util, locale, country_code, dataset)
            entities.append(entity.to_dict())
        return entities
