# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from unittest import mock

from datamimic_ce.domains.common.data_loaders.phone_number_loader import PhoneNumberDataLoader


class TestPhoneNumberDataLoader:
    """Test cases for PhoneNumberDataLoader."""

    def test_init(self):
        """Test initialization of PhoneNumberDataLoader."""
        loader = PhoneNumberDataLoader()
        assert loader.country_code == "US"

        loader = PhoneNumberDataLoader(country_code="fr")
        assert loader.country_code == "FR"

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.Path.exists")
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data="US,en_US,1,United States,331000000\nCA,en_CA,1,Canada,38000000",
    )
    def test_load_country_codes(self, mock_open, mock_exists):
        """Test loading country codes."""
        mock_exists.return_value = True
        loader = PhoneNumberDataLoader()
        country_codes = loader.load_country_codes()

        assert isinstance(country_codes, dict)
        assert "US" in country_codes
        assert country_codes["US"] == "1"
        assert "CA" in country_codes
        assert country_codes["CA"] == "1"

        # Test caching
        mock_open.reset_mock()
        loader.load_country_codes()
        mock_open.assert_not_called()

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.Path.exists")
    @mock.patch(
        "builtins.open",
        new_callable=mock.mock_open,
        read_data="name;areaCode;population\nNew York;212;8000000\nLos Angeles;213;4000000",
    )
    def test_load_area_codes(self, mock_open, mock_exists):
        """Test loading area codes."""
        mock_exists.return_value = True
        loader = PhoneNumberDataLoader()
        area_codes = loader.load_area_codes()

        assert isinstance(area_codes, list)
        assert "212" in area_codes
        assert "213" in area_codes

        # Test caching
        mock_open.reset_mock()
        loader.load_area_codes()
        mock_open.assert_not_called()

    @mock.patch("datamimic_ce.domains.common.data_loaders.phone_number_loader.Path.exists")
    def test_load_area_codes_fallback(self, mock_exists):
        """Test fallback to US area codes when country data is not available."""
        # First call returns False (country file doesn't exist), second call returns True (US file exists)
        mock_exists.side_effect = [False, True]

        # Mock the open function with a context manager to provide different data
        mock_file = mock.mock_open(read_data="name;areaCode;population\nNew York;212;8000000\nLos Angeles;213;4000000")

        with mock.patch("builtins.open", mock_file):
            loader = PhoneNumberDataLoader(country_code="FR")
            area_codes = loader.load_area_codes()

            assert isinstance(area_codes, list)
            # Since we're using default values in the fallback, we should check for those
            assert len(area_codes) > 0
            # The default values should include these area codes
            assert any(code in ["212", "213", "312", "415", "617", "713", "202"] for code in area_codes)

    def test_get_base_paths(self):
        """Test the base path methods."""
        loader = PhoneNumberDataLoader()

        country_path = loader._get_base_path_country()
        assert isinstance(country_path, Path)
        assert country_path.name == "common"

        city_path = loader._get_base_path_city()
        assert isinstance(city_path, Path)
        assert city_path.name == "city"
        assert city_path.parent.name == "common"
