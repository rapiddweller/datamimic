# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDatamimicGenerator:
    _test_dir = Path(__file__).resolve().parent

    def test_date_generate_with_descriptor(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="date_generator_test.xml")
        engine.test_with_timer()

    def test_standalone_generator(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="standalone_generator_test.xml")
        engine.test_with_timer()

    def test_datamimic_demo_generator(self):
        datamimic_dir = (
            Path(__file__).resolve().parent.parent.parent.parent / "datamimic_ce" / "demos" / "overview-generator"
        )
        engine = DataMimicTest(test_dir=datamimic_dir, filename="datamimic.xml")
        engine.test_with_timer()
