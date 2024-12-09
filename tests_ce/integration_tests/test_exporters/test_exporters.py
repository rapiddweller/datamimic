# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestExporter:
    _test_dir = Path(__file__).resolve().parent

    def test_multi_json(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_json.xml")
            test_engine.test_with_timer()

    def test_single_csv(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_csv.xml")
            test_engine.test_with_timer()

    def test_single_combined(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_combine_all.xml")
            test_engine.test_with_timer()

    def test_single_cascaded_cases(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_cascaded_cases.xml")
            test_engine.test_with_timer()

    def test_multi_xml(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_xml.xml")
        test_engine.test_with_timer()
