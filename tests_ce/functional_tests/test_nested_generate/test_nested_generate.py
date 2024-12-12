# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestNestedGenerate:
    _test_dir = Path(__file__).resolve().parent

    def test_nested_generate(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_nested_generate.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()

    def test_generate_as_source(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_generate_as_source.xml", capture_test_result=True
        )
        engine.test_with_timer()
        engine.capture_result()

    def test_generate_as_source_2(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_generate_as_source_2.xml", capture_test_result=True
        )
        engine.test_with_timer()
        engine.capture_result()
