# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSeparator:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert result["product1"] == result["product2"]

    def test_weight_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weight_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert all(len(product) == 2 for product in result["product1"])
        assert all(len(product) == 2 for product in result["product2"])

    def test_weight_ent_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weight_ent_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert all(len(product) == 3 for product in result["people1"])
        assert all(len(product) == 3 for product in result["people2"])

    def test_part(self):
        """Both separators parse the same rows. Unseeded nested keys shuffle independently per statement,
        so the full list is compared as a set and the count-limited list as a subset of it."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_part_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        people1, people2 = result["people1"][0], result["people2"][0]
        by_name = sorted(people1["peopleCsv"], key=lambda person: person["name"])
        assert by_name == sorted(people2["peopleCsv"], key=lambda person: person["name"])
        for short in (people1["shortPeopleCsv"], people2["shortPeopleCsv"]):
            assert len(short) == 2
            assert all(person in by_name for person in short)
