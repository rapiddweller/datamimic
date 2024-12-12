# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.entities.city_entity import CityEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestCityGenerator:
    _supported_dataset = [
        "AD",
        "AL",
        "AT",
        "AU",
        "BA",
        "BE",
        "BG",
        "BR",
        "CA",
        "CH",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LI",
        "LT",
        "LU",
        "LV",
        "MC",
        "NL",
        "NO",
        "NZ",
        "PL",
        "PT",
        "RO",
        "RU",
        "SE",
        "SI",
        "SK",
        "SM",
        "TH",
        "TR",
        "US",
        "US",
        "VA",
        "VE",
        "VN",
    ]

    @staticmethod
    def get_class_factory_util():
        return ClassFactoryCEUtil()

    def test_generate_with_dataset(self):
        for dataset in self._supported_dataset:
            generator = CityEntity(self.get_class_factory_util(), dataset)
            for _ in range(100):
                generated_city = generator
                # check generate city
                assert generated_city is not None, "can not generate city"
                assert isinstance(generated_city, CityEntity)
                # check generate city attributes
                assert generated_city.name is not None, "can not generate city name"
                assert isinstance(generated_city.name, str)
                assert generated_city.postal_code is not None, "can not generate city postal_code"
                assert isinstance(generated_city.postal_code, str)
                assert generated_city.state is not None, "can not generate city state"
                assert isinstance(generated_city.state, str)
                # language is optional
                generated_city.reset()

    def test_city_with_name_extension(self):
        for _ in range(100):
            generated_city = CityEntity(self.get_class_factory_util(), "DE")
            if generated_city.name_extension is not None:
                assert isinstance(generated_city.name_extension, str)
