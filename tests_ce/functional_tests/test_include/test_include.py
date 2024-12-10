# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestInclude:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_include(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_include.xml", capture_test_result=True)
        engine.test_with_timer()

    def test_dynamic_uri_include(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_dynamic_uri.xml", capture_test_result=True)
        engine.test_with_timer()

    def test_dynamic_include_model(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_dynamic_include_model.xml", capture_test_result=True
        )
        engine.test_with_timer()
