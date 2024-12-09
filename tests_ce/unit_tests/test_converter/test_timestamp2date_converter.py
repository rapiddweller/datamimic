# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from datetime import datetime

import pytest

from datamimic_ce.converter.timestamp2date_converter import Timestamp2DateConverter


class TestTimestamp2DateConverter:

    def test_convert_valid_int_timestamp(self):
        converter = Timestamp2DateConverter()
        value = 1696204800  # Corresponds to 2023-10-02 00:00:00
        result = converter.convert(value)
        assert result == datetime.fromtimestamp(value)

    def test_convert_valid_float_timestamp(self):
        converter = Timestamp2DateConverter()
        value = 1696204800.0  # Corresponds to 2023-10-02 00:00:00
        result = converter.convert(value)
        assert result == datetime.fromtimestamp(value)

    def test_convert_invalid_string_timestamp(self):
        converter = Timestamp2DateConverter()
        with pytest.raises(ValueError, match="expect datatype 'int' or 'float'"):
            converter.convert("1696204800")

    def test_convert_none_value(self):
        converter = Timestamp2DateConverter()
        with pytest.raises(ValueError, match="expect datatype 'int' or 'float'"):
            converter.convert(None)

    def test_convert_invalid_list_timestamp(self):
        converter = Timestamp2DateConverter()
        with pytest.raises(ValueError, match="expect datatype 'int' or 'float'"):
            converter.convert([1696204800])
