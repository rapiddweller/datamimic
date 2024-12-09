# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSelector:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_selector(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_selector.xml", capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()

        data = result["data"]

        assert len(data) == 17
        assert data[0]["user_id"] == 1

    def test_iteration_selector(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_iteration_selector.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()

        assert result["simple_data"][:10] == result["iteration_data"][:10]

    def test_dynamic_selector(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_dynamic_selector.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()

        assert len(result["generate_selector"]) == 17

        variable_selector = result["variable_selector"]
        for e in variable_selector:
            assert e.get("name") == f"Name {e.get('id')}"

    def test_edit_dynamic_selector(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_edit_dynamic_selector.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()

        assert len(result["generate_selector"]) == 17

        variable_selector = result["variable_selector"]
        for e in variable_selector:
            assert e.get("name") == f"Name {e.get('id')}"

        assert len(result["generate_selector2"]) == 17

        variable_selector2 = result["variable_selector2"]
        for e in variable_selector2:
            assert e.get("name") == f"Name {e.get('id')}"
