# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestList:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_list(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="test_simple_list.xml",
            capture_test_result=True,
        )
        test_engine.test_with_timer()

        profiles = test_engine.capture_result()["profile"]
        assert len(profiles) == 2
        for profile in profiles:
            assert set(profile) == {"petList"}
            items = profile["petList"]
            assert len(items) == 2
            assert items[0] == {"number": 64}

            pets_item = items[1]
            assert set(pets_item) == {"pets"}
            pets = pets_item["pets"]
            assert len(pets) == 2
            for pet in pets:
                assert set(pet) == {"inner", "str2"}
                assert isinstance(pet["str2"], str)
                assert len(pet["inner"]) == 1
                inner = pet["inner"][0]
                assert set(inner) == {"str1"}
                assert isinstance(inner["str1"], str)

    def test_item_array_child(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="test_item_array_child.xml",
            capture_test_result=True,
        )
        test_engine.test_with_timer()

        rows = test_engine.capture_result()["array_child"]
        assert len(rows) == 2
        for row in rows:
            assert set(row) == {"simple_list"}
            items = row["simple_list"]
            assert len(items) == 2
            assert items[0] == {"name": "Laurence Fishburne", "filmography": ["2", "3", "5"]}

            int_array_item = items[1]
            assert set(int_array_item) == {"int_array"}
            values = int_array_item["int_array"]
            assert len(values) == 10
            assert all(type(value) is int for value in values)
