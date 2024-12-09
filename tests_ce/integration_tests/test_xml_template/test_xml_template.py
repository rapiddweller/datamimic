# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


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
