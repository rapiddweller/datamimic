# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestVariable:
    _test_dir = Path(__file__).resolve().parent

    def test_variable(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable.xml")
        engine.test_with_timer()

    def test_setup_context_variable(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_setup_context_variable.xml")
        engine.test_with_timer()

    def test_query_setup_context_variable(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_query_setup_context_variable.xml")
        engine.test_with_timer()

    def test_variable_with_same_name(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_same_name.xml")
        engine.test_with_timer()

    def test_variable_with_selector(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_selector.xml")
        engine.test_with_timer()

    def test_variable_with_type(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_type.xml")
        engine.test_with_timer()

    def test_variable_source_with_name_only(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_source_with_name_only.xml")
        engine.test_with_timer()

    @pytest.mark.skip("This test is not ready yet.")
    def test_memstore_access(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_memstore_access.xml")
        engine.test_with_timer()

    def test_string_in_key(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_order_status.xml")
        engine.test_with_timer()
