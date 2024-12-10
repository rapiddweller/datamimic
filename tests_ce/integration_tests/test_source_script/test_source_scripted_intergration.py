# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSourceScripted:
    _test_dir = Path(__file__).resolve().parent

    def test_source_scripted(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_scripted.xml", capture_test_result=False)
        engine.test_with_timer()

    def test_default_source_scripted(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_default_source_scripted.xml", capture_test_result=False)
        engine.test_with_timer()

    def test_source_script_in_generate(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_scripted_in_generate.xml", capture_test_result=False)
        engine.test_with_timer()

    def test_source_scripted_in_nested_key(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_scripted_in_nested_key.xml", capture_test_result=False)
        engine.test_with_timer()