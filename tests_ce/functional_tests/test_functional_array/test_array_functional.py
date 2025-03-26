# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestArrayFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_array_script_functional(self) -> None:
        engine = DataMimicTest(test_dir=self._test_dir, filename="functional_test_array.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert result

        array_tag_test = result["array_tag_test"]

        string_script = ["Rose", "Lotus", "Jasmine"]
        int_script = [10, 20, 30]
        float_script = [10.5, 5.8, 7.45]
        bool_script = [True, False, True]

        assert len(array_tag_test) == 50
        for arr in array_tag_test:
            string_array = arr["string_array"]
            assert len(string_array) == 10
            assert isinstance(string_array, list)
            assert all(isinstance(s, str) for s in string_array)

            int_array = arr["int_array"]
            assert len(int_array) == 10
            assert isinstance(int_array, list)
            assert all(isinstance(s, int) for s in int_array)

            float_array = arr["float_array"]
            assert len(float_array) == 10
            assert isinstance(float_array, list)
            assert all(isinstance(s, float) for s in float_array)

            bool_array = arr["bool_array"]
            assert len(bool_array) == 10
            assert isinstance(bool_array, list)
            assert all(isinstance(s, bool) for s in bool_array)

            script_string_array = arr["script_string_array"]
            assert len(script_string_array) == len(string_script)
            assert isinstance(script_string_array, list)
            assert all(isinstance(s, str) for s in script_string_array)
            assert all(s in string_script for s in script_string_array)

            script_int_array = arr["script_int_array"]
            assert len(script_int_array) == len(int_script)
            assert isinstance(script_int_array, list)
            assert all(isinstance(s, int) for s in script_int_array)
            assert all(s in int_script for s in script_int_array)

            script_bool_array = arr["script_bool_array"]
            assert len(script_bool_array) == len(bool_script)
            assert isinstance(script_bool_array, list)
            assert all(isinstance(s, bool) for s in script_bool_array)
            assert all(s in bool_script for s in script_bool_array)

            script_float_array = arr["script_float_array"]
            assert len(script_float_array) == len(float_script)
            assert isinstance(script_float_array, list)
            assert all(isinstance(s, float) for s in script_float_array)
            assert all(s in float_script for s in script_float_array)
