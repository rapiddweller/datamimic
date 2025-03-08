# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.data_loaders.country_loader import CountryDataLoader


class Country(BaseEntity):
    """
    Represents a country with various attributes.

    This class provides access to country data including ISO code, name, language,
    phone code, and population.
    """

    # model_config = ConfigDict(arbitrary_types_allowed=True)

    # iso_code: str = Field(description="The ISO code of the country")
    # name: str = Field(description="The name of the country")
    # default_language_locale: str = Field(description="The default language locale of the country")
    # phone_code: str = Field(description="The phone code of the country")
    # population: str = Field(description="The population of the country")

    # # Private attributes for internal use
    # _property_cache: dict[str, Any] = PrivateAttr(default_factory=dict)

    # # Cache attributes for property_cache decorator
    # _population_int_cache: int | None = PrivateAttr(default=None)

    def __init__(self, data_loader: CountryDataLoader):
        super().__init__()
        self._data_loader = data_loader

    @property
    @property_cache
    def iso_code(self) -> str:
        """Get the ISO code of the country.

        Returns:
            The ISO code of the country
        """
        return self._data_loader.get_random_country()["iso_code"]
    
    @property
    @property_cache
    def country_data(self) -> dict[str, Any]:
        """Get the country data.

        Returns:
            The country data
        """
        return self._data_loader.get_random_country()
    
    @property
    @property_cache
    def name(self) -> str:
        """Get the name of the country.

        Returns:
            The name of the country
        """
        return self._data_loader.get_random_country()["name"]
    
    @property
    @property_cache
    def default_language_locale(self) -> str:
        """Get the default language locale of the country.

        Returns:
            The default language locale of the country
        """
        return self._data_loader.get_random_country()["default_language_locale"]    
    
    @property
    @property_cache
    def phone_code(self) -> str:
        """Get the phone code of the country.

        Returns:
            The phone code of the country
        """
        return self._data_loader.get_random_country()["phone_code"]
    
    @property
    @property_cache
    def population(self) -> str:
        """Get the population of the country.

        Returns:
            The population of the country       
        """
        return self._data_loader.get_random_country()["population"]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the country to a dictionary.

        Returns:
            A dictionary representation of the country
        """
        return {
            "iso_code": self.iso_code,
            "name": self.name,
            "default_language_locale": self.default_language_locale,
            "phone_code": self.phone_code,
            "population": self.population,
        }
    
    