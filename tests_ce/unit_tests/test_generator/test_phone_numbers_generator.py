# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


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
