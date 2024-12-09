# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
