# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestDataSourceCyclic:
    _test_dir = Path(__file__).resolve().parent

    def test_csv_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir,filename= "test_csv_cyclic.xml")
        engine.test_with_timer()

    def test_json_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir,filename= "test_json_cyclic.xml")
        engine.test_with_timer()

    def test_product_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir,filename= "test_product_cyclic.xml")
        engine.test_with_timer()

    def test_variable_memstore_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir,filename= "test_variable_memstore_cyclic.xml")
        engine.test_with_timer()

    def test_variable_database_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir,filename= "test_variable_database_cyclic.xml")
        engine.test_with_timer()
