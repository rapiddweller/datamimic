# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDataMigration:
    _test_dir = Path(__file__).resolve().parent

    def test_postgres(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="datamimic.xml")
        test_engine.test_with_timer()
