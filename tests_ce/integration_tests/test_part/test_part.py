# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPart:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_part(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_part.xml")
        test_engine.test_with_timer()

    def test_source_part_json(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_part_json.xml")
        test_engine.test_with_timer()

    def test_source_part_csv(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_part_csv.xml")
        test_engine.test_with_timer()

    def test_part_within_iterate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="part_in_iterate.xml")
        test_engine.test_with_timer()

    def test_script_dict(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_script_dict.xml")
        test_engine.test_with_timer()
