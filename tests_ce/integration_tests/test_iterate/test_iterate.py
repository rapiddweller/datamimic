# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestIterate:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_iterate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="simple_iterate.xml")
        test_engine.test_with_timer()

    def test_nested_iterate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="nested_iterate.xml")
        test_engine.test_with_timer()
