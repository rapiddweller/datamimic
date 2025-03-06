# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any
import random
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domains.common.data_loaders.address_loader import AddressDataLoader
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator


class Address(BaseEntity):
    """
    Represents an address with various components.

    This class provides access to address data including street, house number, city,
    state, postal code, country, and more.
    """
    def __init__(self, data_loader: AddressDataLoader):
        super().__init__()
        self._data_loader = data_loader
        self._phone_number_generator = PhoneNumberGenerator()

    @property
    @property_cache
    def street(self) -> str:
        street_data = self._data_loader.load_street_data()
        return random.choice(street_data) if street_data else "Main Street"
    
    @property
    @property_cache
    def house_number(self) -> str:
        house_number_data = self._data_loader.load_house_numbers()
        return random.choice(house_number_data) if house_number_data else "123"
    
    #TODO: rework city data loader
    # @property
    # @property_cache
    # def city_data(self) -> str:
    #     return self._data_loader.city_loader.get_random_city()
    
    # @property
    # @property_cache
    # def city(self) -> str:
    #     return self.city_data["name"]
    
    # @property
    # @property_cache
    # def state(self) -> str:
    #     return self.city_data["state"]
    
    # @property
    # @property_cache
    # def postal_code(self) -> str:
    #     return self.city_data["postal_code"]
    
    #TODO: rework country data loader
    # @property
    # @property_cache
    # def country_data(self) -> str:
    #     return self._data_loader.country_loader.get_country_by_iso_code(self.country_code)
    
    # @property
    # @property_cache
    # def country(self) -> str:
    #     return self.country_data["name"]
    
    @property
    @property_cache
    def country_code(self) -> str:
        return self._data_loader.country_code
    
    @property
    @property_cache
    def phone(self) -> str:
        return self._phone_number_generator.generate()
    
    @property
    @property_cache
    def mobile_phone(self) -> str:
        return self._phone_number_generator.generate()
    
    @property
    @property_cache
    def fax(self) -> str:
        return self._phone_number_generator.generate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "street": self.street,
            "house_number": self.house_number,
            # "city": self.city,
            # "state": self.state,
            # "postal_code": self.postal_code,
            # "country": self.country,
            "country_code": self.country_code,
            "phone": self.phone,
            "mobile_phone": self.mobile_phone,
            "fax": self.fax,
        }
