# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


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
            assert active_value is None
