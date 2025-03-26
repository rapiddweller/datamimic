# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestXMLTemplate:
    _test_dir = Path(__file__).resolve().parent

    def test_xml_template(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_template.xml", capture_test_result=False)
        engine.test_with_timer()

    def test_xml_template_2(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_xml_template_2.xml", capture_test_result=False)
        engine.test_with_timer()

    def test_simple_xml_generate(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_simple_xml_generate.xml", capture_test_result=False
        )
        engine.test_with_timer()

    def test_xml_template_script(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_xml_template_script.xml", capture_test_result=False
        )
        engine.test_with_timer()

    def test_casting_xml_value(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_casting_xml_value.xml", capture_test_result=False
        )
        engine.test_with_timer()
