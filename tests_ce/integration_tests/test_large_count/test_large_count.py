# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestLargeCount:
    _test_dir = Path(__file__).resolve().parent

    def test_large_count(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count.xml")
        engine.test_with_timer()

    def test_large_count_2(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_2.xml")
        engine.test_with_timer()

    def test_builders(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_entities.xml")
        engine.test_with_timer()

    def test_generators(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_generators.xml")
        engine.test_with_timer()

    def test_new_builders(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_new_builders.xml")
        engine.test_with_timer()

    def test_large_count_small_page(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_small_page.xml")
        engine.test_with_timer()
