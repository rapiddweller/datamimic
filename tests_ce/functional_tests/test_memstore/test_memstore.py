# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestMemStore:
    _test_dir = Path(__file__).resolve().parent

    def test_in_memory_memstore(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_in_memory_memstore.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()
        assert len(result["data"]) == 100000
        assert len(result["data2"]) == len(result["data"])

    def test_memstore_in_nested_generate_with_mp(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_memstore_in_nested_generate_with_mp.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()

        wrapping = result["wrapping"]
        assert len(wrapping) == 2

        data_1 = result["iterate_1"]
        assert len(data_1) == 20
        count_data_1 = 0
        for element_data_1 in data_1:
            count_data_1 += 1
            if count_data_1 > 10:
                assert element_data_1["id"] == f"2_{count_data_1 - 10}"
            else:
                assert element_data_1["id"] == f"1_{count_data_1}"
            assert isinstance(element_data_1["name"], str)

        data_2 = result["iterate_2"]
        assert len(data_2) == 20
        count_data_2 = 0
        for element_data_2 in data_2:
            count_data_2 += 1
            if count_data_2 > 10:
                assert element_data_2["id"] == f"2_{count_data_2 - 10}"
            else:
                assert element_data_2["id"] == f"1_{count_data_2}"
            assert isinstance(element_data_2["number"], int)
