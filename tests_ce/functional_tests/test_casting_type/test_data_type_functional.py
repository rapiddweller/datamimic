# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from types import NoneType

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDataType:
    _test_dir = Path(__file__).resolve().parent

    def test_data_type(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_data_type.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        products = result["product"]

        assert len(products) == 50
        for product in products:
            # constant default type is str
            assert type(product["hello_constant"]) == str
            assert type(product["none_constant"]) == str
            assert type(product["empty_constant"]) == str

            # values default type base on python type evaluate
            assert type(product["age"]) == int
            assert type(product["GPA"]) == float or int
            assert type(product["active"]) == bool
            assert type(product["inactive"]) == bool
            assert isinstance(product["none_values"], NoneType)
            assert isinstance(product["none_script"], NoneType)
            assert type(product["random_str_numbers"]) == str
            assert product["random_str_numbers"] in ["1,2,3,4", "1,2,3", "1,2"]
            assert isinstance(product["random_list_numbers"], list)
            assert isinstance(product["random_tuple_numbers"], tuple)
            assert isinstance(product["random_set_numbers"], set)
            assert isinstance(product["random_dict_numbers"], dict)

            # convert type
            assert type(product["hello_constant_string_type"]) == str
            assert type(product["age_int_type"]) == int
            assert type(product["GPA_float_type"]) == float
            assert type(product["active_bool_type"]) == bool
            assert product["active_bool_type"] is True
            assert type(product["inactive_bool_type"]) == bool
            assert product["inactive_bool_type"] is False
