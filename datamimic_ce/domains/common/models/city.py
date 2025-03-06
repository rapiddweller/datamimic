# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.data_loaders.city_loader import CityDataLoader


class City(BaseEntity):
    """
    Represents a city with various attributes.

    This class provides access to city data including name, postal code, area code,
    state, language, population, and country information.
    """


    # name: str = Field(description="The name of the city")
    # postal_code: str = Field(description="The postal code of the city")
    # area_code: str = Field(description="The area code of the city")
    # state_id: str = Field(description="The ID of the state where the city is located")
    # state: str = Field(description="The name of the state where the city is located")
    # language: str | None = Field(None, description="The language spoken in the city")
    # population: str = Field(description="The population of the city")
    # name_extension: str = Field("", description="The name extension of the city")
    # country: str = Field(description="The country where the city is located")
    # country_code: str = Field(description="The country code of the city")

    # # Cache attributes for property_cache decorator
    # _full_name_cache: str | None = PrivateAttr(default=None)
    # _location_string_cache: str | None = PrivateAttr(default=None)
    # _population_int_cache: int | None = PrivateAttr(default=None)

    def __init__(self, data_loader: CityDataLoader):
        super().__init__()
        self._data_loader = data_loader

    @property
    @property_cache
    def city_data(self) -> dict[str, Any]:
        """Get the city data.

        Returns:
            The city data.
        """
        return self._data_loader.get_random_city()
    
    @property
    @property_cache
    def name(self) -> str:
        """Get the name of the city.

        Returns:
            The name of the city.
        """
        return self.city_data["name"]
    
    @property
    @property_cache
    def postal_code(self) -> str:
        """Get the postal code of the city.

        Returns:
            The postal code of the city.
        """
        return self.city_data["postal_code"]

    @property
    @property_cache
    def area_code(self) -> str:
        """Get the area code of the city.

        Returns:
            The area code of the city.
        """
        return self.city_data["area_code"]

    @property
    @property_cache
    def state_id(self) -> str:
        """Get the state ID of the city.

        Returns:
            The state ID of the city.
        """
        return self.city_data["state_id"]

    @property
    @property_cache
    def state(self) -> str:
        """Get the state of the city.

        Returns:
            The state of the city.
        """
        return self.city_data["state"]

    @property
    @property_cache
    def language(self) -> str | None:
        """Get the language of the city.

        Returns:
            The language of the city.
        """
        return self.city_data["language"]
    
    @property
    @property_cache
    def population(self) -> str:
        """Get the population of the city.

        Returns:
            The population of the city.
        """
        return self.city_data["population"]
    
    @property
    @property_cache
    def name_extension(self) -> str:
        """Get the name extension of the city.

        Returns:
            The name extension of the city.
        """
        return self.city_data["name_extension"]

    @property
    @property_cache
    def country(self) -> str:
        """Get the country of the city.

        Returns:
            The country of the city.
        """
        return self.city_data["country"]
    
    @property
    @property_cache
    def country_code(self) -> str:
        """Get the country code of the city.

        Returns:
            The country code of the city.   

        """
        return self.city_data["country_code"]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the city to a dictionary.

        Returns:    
            A dictionary representation of the city.
        """
        return {
            "name": self.name,
            "postal_code": self.postal_code,
            "area_code": self.area_code,
            "state_id": self.state_id,
            "state": self.state,
            "language": self.language,
            "population": self.population,
            "name_extension": self.name_extension,
            "country": self.country,
            "country_code": self.country_code
        }
    