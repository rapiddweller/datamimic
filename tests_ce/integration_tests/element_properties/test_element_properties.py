# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestElementProperties:
    _test_dir = Path(__file__).resolve().parent

    def test_script(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_script.xml")
        engine.test_with_timer()

    def test_formatted_string(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_formatted_string.xml")
        engine.test_with_timer()
