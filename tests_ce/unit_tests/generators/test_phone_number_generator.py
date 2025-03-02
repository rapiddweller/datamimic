# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from unittest import mock

from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator


class TestPhoneNumberGenerator:
    """Test cases for PhoneNumberGenerator."""

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_area_codes")
    def test_init(self, mock_load_area_codes, mock_load_country_codes):
        """Test initialization of PhoneNumberGenerator."""
        mock_load_country_codes.return_value = {"US": "1", "CA": "1", "UK": "44"}
        mock_load_area_codes.return_value = ["212", "213", "312"]

        # Test with default parameters
        generator = PhoneNumberGenerator()
        assert generator._dataset == "US"
        assert generator._is_mobile is False
        assert len(generator._area_data) == 3

        # Test with custom dataset
        generator = PhoneNumberGenerator(dataset="UK")
        assert generator._dataset == "UK"

        # Test with custom area code
        generator = PhoneNumberGenerator(area_code="999")
        assert generator._area_data == ["999"]

        # Test with is_mobile=True
        generator = PhoneNumberGenerator(is_mobile=True)
        assert generator._is_mobile is True
        assert not hasattr(generator, "_area_data")

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_area_codes")
    def test_generate_non_mobile(self, mock_load_area_codes, mock_load_country_codes):
        """Test generating a non-mobile phone number."""
        mock_load_country_codes.return_value = {"US": "1"}
        mock_load_area_codes.return_value = ["212"]

        generator = PhoneNumberGenerator()
        phone_number = generator.generate()

        assert phone_number.startswith("+1-212-")
        assert len(phone_number) == 14  # +1-212-XXXXXXX format

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    def test_generate_mobile(self, mock_load_country_codes):
        """Test generating a mobile phone number."""
        mock_load_country_codes.return_value = {"US": "1"}

        generator = PhoneNumberGenerator(is_mobile=True)
        phone_number = generator.generate()

        assert phone_number.startswith("+1-")
        assert len(phone_number) == 14  # +1-XXX-XXXXXXX format

        # Extract the area code
        area_code = phone_number.split("-")[1]
        assert len(area_code) == 3
        assert 100 <= int(area_code) <= 999

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_area_codes")
    def test_generate_with_empty_area_codes(self, mock_load_area_codes, mock_load_country_codes):
        """Test generating a phone number when area codes list is empty."""
        mock_load_country_codes.return_value = {"US": "1"}
        mock_load_area_codes.return_value = []

        generator = PhoneNumberGenerator()
        phone_number = generator.generate()

        assert phone_number.startswith("+1-0-")
        # The length can vary based on the implementation, but should be consistent
        # with the format +1-0-XXXXXXXXX
        assert len(phone_number) == 14  # +1-0-XXXXXXXXX format

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_area_codes")
    def test_generate_with_missing_country_code(self, mock_load_area_codes, mock_load_country_codes):
        """Test generating a phone number when country code is missing."""
        mock_load_country_codes.return_value = {}
        mock_load_area_codes.return_value = ["212"]

        generator = PhoneNumberGenerator()
        phone_number = generator.generate()

        assert phone_number.startswith("+0-212-")
        assert len(phone_number) == 14  # +0-212-XXXXXXX format

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_country_codes")
    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.PhoneNumberDataLoader.load_area_codes")
    def test_generate_with_empty_country_code(self, mock_load_area_codes, mock_load_country_codes):
        """Test generating a phone number when country code is empty."""
        mock_load_country_codes.return_value = {"US": ""}
        mock_load_area_codes.return_value = ["212"]

        generator = PhoneNumberGenerator()
        phone_number = generator.generate()

        assert phone_number.startswith("+0-212-")
        assert len(phone_number) == 14  # +0-212-XXXXXXX format
