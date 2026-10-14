# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


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

    def test_memstore_access(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_memstore_access.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()
        users = result["user"]
        selected_users = result["user_2"]

        assert [user["id"] for user in users] == [1, 2, 3, 4, 5]
        assert all(isinstance(user["name"], str) for user in users)
        assert len(selected_users) == 3
        assert len({user["id"] for user in selected_users}) == 3
        names_by_id = {user["id"]: user["name"] for user in users}
        assert all(user["name"] == names_by_id[user["id"]] for user in selected_users)

    def test_string_in_key(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_order_status.xml")
        engine.test_with_timer()
