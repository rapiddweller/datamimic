# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any
import random
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader


class Address:
    """
    Represents an address with various components.

    This class provides access to address data including street, house number, city,
    state, postal code, country, and more.
    """
    def __init__(self, data_loader: AddressDataLoader):
        self.data_loader = data_loader


    # # Basic address components
    # street: str = Field(description="The street name")
    # house_number: str = Field(description="The house or building number")
    # city: str = Field(description="The city name")
    # state: str = Field(description="The state, province, or administrative region")
    # postal_code: str = Field(description="The postal or zip code")
    # country: str = Field(description="The country name")
    # country_code: str = Field(description="The ISO country code")

    # # Optional components
    # continent: str | None = Field(None, description="The continent name")
    # latitude: float | None = Field(None, description="The latitude coordinate")
    # longitude: float | None = Field(None, description="The longitude coordinate")
    # organization: str | None = Field(None, description="The organization or company name")

    # # Contact information
    # phone: str | None = Field(None, description="A phone number")
    # mobile_phone: str | None = Field(None, description="A mobile phone number")
    # fax: str | None = Field(None, description="A fax number")

    @property
    @property_cache
    def street(self) -> str:
        street_data = self.data_loader.load_street_data()
        return random.choice(street_data) if street_data else "Main Street"
    
    @property
    @property_cache
    def house_number(self) -> str:
        house_number_data = self.data_loader.load_house_numbers()
        return random.choice(house_number_data) if house_number_data else "123"
    
    # @property
    # @property_cache
    # def city(self) -> str:
    #     city_data = self.data_loader.city_loader.get_random_city()
    #     return random.choice(city_data) if city_data else "New York"
    

    # Private attributes for internal use
    # _property_cache: dict[str, Any] = PrivateAttr(default_factory=dict)

    # Cache attributes for property_cache decorator
    # _formatted_address_cache: str | None = PrivateAttr(default=None)
    # _coordinates_cache: dict[str, float] | None = PrivateAttr(default=None)

    # @classmethod
    # def create(cls, data: dict[str, Any]) -> "Address":
    #     """
    #     Create an Address instance from a dictionary of data.

    #     Args:
    #         data: Dictionary containing address data

    #     Returns:
    #         A new Address instance
    #     """
    #     return cls(**data)

    # @property
    # @property_cache
    # def formatted_address(self) -> str:
    #     """
    #     Get the formatted address according to local conventions.

    #     Returns:
    #         The formatted address as a string
    #     """
    #     # North American format (US, CA)
    #     if self.country_code in ["US", "CA"]:
    #         return f"{self.house_number} {self.street}\n{self.city}, {self.state} {self.postal_code}\n{self.country}"

    #     # UK format
    #     elif self.country_code in ["GB", "IE"]:
    #         return f"{self.house_number} {self.street}\n{self.city}\n{self.state}\n{self.postal_code}\n{self.country}"

    #     # German/Central European format
    #     elif self.country_code in ["DE", "AT", "CH", "NL", "BE", "LU", "CZ", "SK", "PL", "HU", "SI", "HR"]:
    #         return f"{self.street} {self.house_number}\n{self.postal_code} {self.city}\n{self.state}\n{self.country}"

    #     # French format
    #     elif self.country_code in ["FR", "MC"]:
    #         return f"{self.house_number} {self.street}\n{self.postal_code} {self.city}\n{self.state}\n{self.country}"

    #     # Default format
    #     else:
    #         return f"{self.house_number} {self.street}\n{self.city}, {self.state} {self.postal_code}\n{self.country}"

    # @property
    # @property_cache
    # def coordinates(self) -> dict[str, float]:
    #     """
    #     Get the coordinates as a dictionary.

    #     Returns:
    #         A dictionary with latitude and longitude
    #     """
    #     return {
    #         "latitude": self.latitude if self.latitude is not None else 0.0,
    #         "longitude": self.longitude if self.longitude is not None else 0.0,
    #     }

    # @property
    # def zip_code(self) -> str:
    #     """
    #     Alias for postal_code.

    #     Returns:
    #         The postal code
    #     """
    #     return self.postal_code

    # def to_dict(self) -> dict[str, Any]:
    #     """
    #     Convert the address to a dictionary.

    #     Returns:
    #         A dictionary representation of the address
    #     """
    #     return self.model_dump(exclude={"_property_cache"})

    # def reset(self) -> None:
    #     """
    #     Reset all cached properties.
    #     """
    #     self._property_cache = {}
    #     self._formatted_address_cache = None
    #     self._coordinates_cache = None
