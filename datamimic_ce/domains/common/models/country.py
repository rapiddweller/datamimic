# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.core.property_cache import property_cache


class Country(BaseModel):
    """
    Represents a country with various attributes.

    This class provides access to country data including ISO code, name, language,
    phone code, and population.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    iso_code: str = Field(description="The ISO code of the country")
    name: str = Field(description="The name of the country")
    default_language_locale: str = Field(description="The default language locale of the country")
    phone_code: str = Field(description="The phone code of the country")
    population: str = Field(description="The population of the country")

    # Private attributes for internal use
    _property_cache: dict[str, Any] = PrivateAttr(default_factory=dict)

    # Cache attributes for property_cache decorator
    _population_int_cache: int | None = PrivateAttr(default=None)

    @classmethod
    def create(cls, data: dict[str, Any]) -> "Country":
        """
        Create a Country instance from a dictionary of data.

        Args:
            data: Dictionary containing country data

        Returns:
            A new Country instance
        """
        return cls(**data)

    @property
    @property_cache
    def population_int(self) -> int:
        """
        Get the population as an integer.

        Returns:
            The population as an integer
        """
        try:
            return int(self.population)
        except (ValueError, TypeError):
            return 0

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the country to a dictionary.

        Returns:
            A dictionary representation of the country
        """
        return self.model_dump(exclude={"_property_cache"})

    def reset(self) -> None:
        """
        Reset all cached properties.
        """
        self._property_cache = {}
        self._population_int_cache = None
