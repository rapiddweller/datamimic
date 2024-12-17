# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.entities.city_entity import CityEntity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.generators.street_name_generator import StreetNameGenerator


class AddressEntity:
    """
    Represents an address entity with various attributes.

    This class provides methods to generate and access address-related data.
    """

    def __init__(self, class_factory_util, dataset: str = "US"):
        """
        Initialize the AddressEntity.

        Args:
            class_factory_util: The class factory utility.
            dataset (str): The dataset to be used. Defaults to "US".
        """
        self._street_name_gen = StreetNameGenerator(dataset=dataset)
        self._city_entity = CityEntity(class_factory_util, dataset=dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=dataset)
        self._company_name_generator = CompanyNameGenerator()

        data_generation_util = class_factory_util.get_data_generation_util()

        generator_fn_dict = {
            "organization": lambda: self._company_name_generator.generate(),
            "office_phone": lambda: self._phone_number_generator.generate(),
            "private_phone": lambda: self._phone_number_generator.generate(),
            "mobile_phone": lambda: self._phone_number_generator.generate(),
            "fax": lambda: self._phone_number_generator.generate(),
            "street": lambda: self._street_name_gen.generate(),
            "house_number": lambda: str(data_generation_util.rnd_int(1, 9999)),
            "city_entity": lambda: self._city_entity,
        }
        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def street(self):
        """
        Get the street name.

        Returns:
            str: The street name.
        """
        return self._field_generator["street"].get()

    @property
    def house_number(self):
        """
        Get the house number.

        Returns:
            str: The house number.
        """
        return self._field_generator["house_number"].get()

    @property
    def city(self):
        """
        Get the city name.

        Returns:
            str: The city name.
        """
        return self._field_generator["city_entity"].get().name

    @property
    def state(self):
        """
        Get the state name.

        Returns:
            str: The state name.
        """
        return self._field_generator["city_entity"].get().state

    @property
    def area(self):
        """
        Get the area code.

        Returns:
            str: The area code.
        """
        return self._field_generator["city_entity"].get().area_code

    @property
    def country(self):
        """
        Get the country name.

        Returns:
            str: The country name.
        """
        return self._field_generator["city_entity"].get().country

    @property
    def country_code(self):
        """
        Get the country code.

        Returns:
            str: The country code.
        """
        return self._field_generator["city_entity"].get().country_code

    @property
    def zip_code(self):
        """
        Get the zip code.

        Returns:
            str: The zip code.
        """
        return self._field_generator["city_entity"].get().postal_code

    @property
    def postal_code(self):
        """
        Get the postal code.

        Returns:
            str: The postal code.
        """
        return self._field_generator["city_entity"].get().postal_code

    @property
    def office_phone(self):
        """
        Get the office phone number.

        Returns:
            str: The office phone number.
        """
        return self._field_generator["office_phone"].get()

    @property
    def private_phone(self):
        """
        Get the private phone number.

        Returns:
            str: The private phone number.
        """
        return self._field_generator["private_phone"].get()

    @property
    def mobile_phone(self):
        """
        Get the mobile phone number.

        Returns:
            str: The mobile phone number.
        """
        return self._field_generator["mobile_phone"].get()

    @property
    def fax(self):
        """
        Get the fax number.

        Returns:
            str: The fax number.
        """
        return self._field_generator["fax"].get()

    @property
    def organization(self):
        """
        Get the organization name.

        Returns:
            str: The organization name.
        """
        return self._field_generator["organization"].get()

    def reset(self):
        """
        Reset the field generators and city entity.
        """
        for key in self._field_generator:
            self._field_generator[key].reset()
        self._city_entity.reset()
