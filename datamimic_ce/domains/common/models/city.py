# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.core.property_cache import property_cache


class City(BaseModel):
    """
    Represents a city with various attributes.

    This class provides access to city data including name, postal code, area code,
    state, language, population, and country information.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="The name of the city")
    postal_code: str = Field(description="The postal code of the city")
    area_code: str = Field(description="The area code of the city")
    state_id: str = Field(description="The ID of the state where the city is located")
    state: str = Field(description="The name of the state where the city is located")
    language: str | None = Field(None, description="The language spoken in the city")
    population: str = Field(description="The population of the city")
    name_extension: str = Field("", description="The name extension of the city")
    country: str = Field(description="The country where the city is located")
    country_code: str = Field(description="The country code of the city")

    # Private attributes for internal use
    _dataset: str = PrivateAttr(default="US")
    _property_cache: dict[str, Any] = PrivateAttr(default_factory=dict)

    # Cache attributes for property_cache decorator
    _full_name_cache: str | None = PrivateAttr(default=None)
    _location_string_cache: str | None = PrivateAttr(default=None)
    _population_int_cache: int | None = PrivateAttr(default=None)

    @classmethod
    def create(cls, data: dict[str, Any]) -> "City":
        """
        Create a City instance from a dictionary of data.

        Args:
            data: Dictionary containing city data

        Returns:
            A new City instance
        """
        return cls(**data)

    @property
    @property_cache
    def full_name(self) -> str:
        """
        Get the full name of the city including any extension.

        Returns:
            The full name of the city
        """
        if self.name_extension:
            return f"{self.name} {self.name_extension}"
        return self.name

    @property
    @property_cache
    def location_string(self) -> str:
        """
        Get a formatted location string for the city.

        Returns:
            A string in the format "City, State, Country"
        """
        components = [self.name]
        if self.state:
            components.append(self.state)
        if self.country:
            components.append(self.country)
        return ", ".join(components)

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
        Convert the city to a dictionary.

        Returns:
            A dictionary representation of the city
        """
        return self.model_dump(exclude={"_property_cache", "_dataset"})

    def reset(self) -> None:
        """
        Reset all cached properties.
        """
        self._property_cache = {}
        self._full_name_cache = None
        self._location_string_cache = None
        self._population_int_cache = None
