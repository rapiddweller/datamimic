# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
