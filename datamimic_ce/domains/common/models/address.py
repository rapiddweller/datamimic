# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator


class Address(BaseEntity):
    """
    Represents an address with various components.

    This class provides access to address data including street, house number, city,
    state, postal code, country, and more.
    """
    def __init__(self, address_generator: AddressGenerator):
        super().__init__()
        # IMPORTANT: Avoid init generator in __init__ method, because it will be called multiple times
        # Should define generator within dataloader instead
        self._address_generator = address_generator
        

    @property
    @property_cache
    def street(self) -> str:
        return self._address_generator.generate_street_name()
    
    @property
    @property_cache
    def house_number(self) -> str:
        return self._address_generator.generate_house_number()
    
    @property
    @property_cache
    def city_data(self) -> str:
        return self._address_generator.city_generator.get_random_city()
    
    @property
    @property_cache
    def city(self) -> str:
        return self.city_data["name"]
    
    @property
    @property_cache
    def area(self) -> str:
        return self.city_data["area_code"]
    
    @property
    @property_cache
    def state(self) -> str:
        return self.city_data["state"]
    
    @property
    @property_cache
    def postal_code(self) -> str:
        return self.city_data["postal_code"]
    
    @property
    @property_cache
    def zip_code(self) -> str:
        return self.postal_code
    
    @property
    @property_cache
    def country_data(self) -> str:
        return self._address_generator.country_generator.get_country_by_iso_code(self.country_code)
    
    @property
    @property_cache
    def country(self) -> str:
        return self.country_data[4]
    
    @property
    @property_cache
    def country_code(self) -> str:
        return self._address_generator.country_code
    
    @property
    @property_cache
    def phone(self) -> str:
        return self._address_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def mobile_phone(self) -> str:
        return self._address_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def office_phone(self) -> str:
        return self._address_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def private_phone(self) -> str:
        return self._address_generator.phone_number_generator.generate()
    
    @property
    @property_cache
    def fax(self) -> str:
        return self._address_generator.phone_number_generator.generate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "street": self.street,
            "house_number": self.house_number,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "country_code": self.country_code,
            "phone": self.phone,
            "mobile_phone": self.mobile_phone,
            "fax": self.fax,
        }
