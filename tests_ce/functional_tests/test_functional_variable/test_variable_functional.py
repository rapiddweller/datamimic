# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestVariableFunctional:
    _test_dir = Path(__file__).resolve().parent

    def test_query_setup_context_variable(self):
        engine = DataMimicTest(test_dir=self._test_dir,
                               filename="test_query_setup_context_variable.xml",
                               capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        query_variable_test = result.get('query_variable_test')
        assert len(query_variable_test) == 10
        for element in query_variable_test:
            assert element.get("id") in [1, 2, 3]
            assert element.get("name") in ['Name 1', 'Name 2', 'Name 3']
            if element.get("id") == 1:
                assert element.get("name") == 'Name 1'
            elif element.get("id") == 2:
                assert element.get("name") == 'Name 2'
            elif element.get("id") == 3:
                assert element.get("name") == 'Name 3'
            assert element.get("static_id") == 1
            assert element.get("static_name") == 'Name 1'

    def test_variable_with_type(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_type.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        variable_with_type = result["user"]
        assert len(variable_with_type) == 10
        for ele in variable_with_type:
            assert ele.get("table_id") == 1
            assert ele.get("table_name") == "Name 1"
            assert ele.get("table_number") == 1

        user_2 = result["user_2"]
        assert len(user_2) == len(variable_with_type)
        count = 0
        for ele in user_2:
            count += 1
            assert ele.get("id") == count
            assert ele.get("name") == "Name 1"
            assert ele.get("number") == 1

    def test_variable_source_with_name_only(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_source_with_name_only.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        variable_with_type = result["user"]
        assert len(variable_with_type) == 10
        for ele in variable_with_type:
            assert ele.get("id") == 1
            assert ele.get("name") == "Name 1"
            assert ele.get("number") == 1

    def test_variable_with_selector_cyclic(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_selector_cyclic.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        user = result["user"]
        assert len(user) == 3
        assert all(ele.get("id") in [1, 2, 3] for ele in user)

        selector_cyclic = result["selector_cyclic"]
        assert len(selector_cyclic) == 10
        assert all(ele.get("user_id") in [1, 2, 3] for ele in selector_cyclic)
        for ele in selector_cyclic:
            if ele.get("user_id") == 1:
                assert ele.get("user_text") == "Name 1"
            elif ele.get("user_id") == 2:
                assert ele.get("user_text") == "Name 2"
            elif ele.get("user_id") == 3:
                assert ele.get("user_text") == "Name 3"

        iteration_selector_cyclic = result["iteration_selector_cyclic"]
        assert len(iteration_selector_cyclic) == 10
        for ele in iteration_selector_cyclic:
            if ele.get("user_id") == 1:
                assert ele.get("user_text") == "Name 1"
            elif ele.get("user_id") == 2:
                assert ele.get("user_text") == "Name 2"
            elif ele.get("user_id") == 3:
                assert ele.get("user_text") == "Name 3"

