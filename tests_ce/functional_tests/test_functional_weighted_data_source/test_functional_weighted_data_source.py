# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



import math
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestWeightedDataSourceFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_weight_data_source(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="weighted_csv_file.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()

        assert result

        people_from_source = result["people_from_source"]

        expect_length_result = 100

        assert len(people_from_source) == expect_length_result

        for people in people_from_source:
             active_value = people["active"]
             if active_value is not None:
                 assert not math.isnan(active_value), f"Active value is NaN for {people}"


