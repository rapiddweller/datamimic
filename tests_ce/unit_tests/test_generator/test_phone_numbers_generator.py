# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator


class TestPhoneNumberGenerator:
    def test_phone_number_generator(self):
        for _ in range(10):
            phone_number = PhoneNumberGenerator().generate()
            assert phone_number
            assert isinstance(phone_number, str)

    def test_phone_number_generator_specific_dataset(self):
        for _ in range(10):
            phone_number = PhoneNumberGenerator(dataset="DE").generate()
            assert phone_number
            assert isinstance(phone_number, str)
            assert phone_number.startswith("+49-")

    def test_phone_number_generator_not_exist_dataset(self):
        # if dataset not exist -> use US dataset
        for _ in range(10):
            phone_number = PhoneNumberGenerator(dataset="SV").generate()
            assert phone_number
            assert isinstance(phone_number, str)
            assert phone_number.startswith("+1-")

    def test_phone_number_generator_none_country_code(self):
        # if dataset not exist -> use US dataset
        for _ in range(10):
            phone_number_generator = PhoneNumberGenerator()
            assert phone_number_generator._dataset == "US"
            phone_number_generator._country_codes = {"US": None}
            phone_number = phone_number_generator.generate()
            assert phone_number
            assert isinstance(phone_number, str)
            assert phone_number.startswith("+0-")
