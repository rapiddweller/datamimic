# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datetime import datetime

import pytest

from datamimic_ce.converter.date2timestamp_converter import Date2TimestampConverter


class TestDate2TimestampConverter:
    def test_convert_valid_datetime(self):
        converter = Date2TimestampConverter()
        value = datetime(2023, 10, 1, 12, 0, 0)
        result = converter.convert(value)
        assert result == int(value.timestamp())

    def test_convert_invalid_type(self):
        converter = Date2TimestampConverter()
        with pytest.raises(ValueError, match="expect datatype 'datetime'"):
            converter.convert("2023-10-01 12:00:00")

    def test_convert_none_value(self):
        converter = Date2TimestampConverter()
        with pytest.raises(ValueError, match="expect datatype 'datetime'"):
            converter.convert(None)
