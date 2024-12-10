# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestWeightedDataSource:
    _test_dir = Path(__file__).resolve().parent

    def test_weighted_datasource(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weighted_entity_data_source.xml")
        engine.test_with_timer()

    def test_weighted_datasource_with_weight_column(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_weighted_entity_data_source_weight_column.xml")
        engine.test_with_timer()

    def test_weight_data_source(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="weighted_csv_file.xml")
        engine.test_with_timer()
