# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDataIteration:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert result["product1"] == result["product2"]

    def test_weight_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weight_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert all(len(product) == 2 for product in result["product1"])
        assert all(len(product) == 2 for product in result["product2"])

    def test_weight_ent_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weight_ent_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert all(len(product) == 3 for product in result["people1"])
        assert all(len(product) == 3 for product in result["people2"])

    def test_part(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_part_csv.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        assert result["people1"] == result["people2"]
